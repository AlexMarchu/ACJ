import requests
from django.http import JsonResponse
from django.urls import reverse_lazy
from django.shortcuts import get_object_or_404, render
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_POST
from django.db.models import Q, Prefetch
from django.utils import timezone
from django.contrib.auth.mixins import UserPassesTestMixin
from django.views.generic import CreateView
from rest_framework import viewsets, permissions, status
from rest_framework.decorators import api_view
from rest_framework.response import Response
from channels.layers import get_channel_layer
from asgiref.sync import async_to_sync

from contests.models import Contest, ContestProblem
from problems.models import SubmissionStatus, Language, Problem, Test, SubmissionContent, Submission, \
    SubmissionTestResult, ProblemTag
from problems.permissions import IsAdminOrTeacher
from problems.serializers import ProblemSerializer, TestSerializer
from problems.forms import ProblemForm, TestFormSet, TestForm

class ProblemViewSet(viewsets.ModelViewSet):

    queryset = Problem.objects.all()
    serializer_class = ProblemSerializer

    def get_permissions(self):
        if self.action in ["create", "update", "partial_update", "destroy"]:
            return [permissions.IsAuthenticated(), IsAdminOrTeacher()]
        return [permissions.IsAuthenticated()]


class TestViewSet(viewsets.ModelViewSet):

    queryset = Test.objects.all()
    serializer_class = TestSerializer

    def get_permissions(self):
        if self.action in ["create", "update", "partial_update", "destroy"]:
            return [permissions.IsAuthenticated(), IsAdminOrTeacher()]
        return [permissions.IsAuthenticated()]


class CreateProblemView(UserPassesTestMixin, CreateView):
    
    model = Problem
    form_class = ProblemForm
    template_name = "problems/create_problem.html"
    success_url = reverse_lazy("home")

    def test_func(self):
        return self.request.user.is_teacher() or self.request.user.is_admin()
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        if self.request.POST:
            context["test_formset"] = TestFormSet(self.request.POST)
        else:
            context["test_formset"] = TestFormSet()
        return context
    
    def form_valid(self, form):
        context = self.get_context_data()
        test_formset = context["test_formset"]
        if test_formset.is_valid():
            self.object = form.save(commit=False)
            self.object.author = self.request.user
            self.object.save()

            test_formset.instance = self.object
            test_formset.save()
            return super().form_valid(form)
        else:
            return self.form_invalid(form)


def problem_detail(request, problem_id):
    problem = get_object_or_404(Problem, id=problem_id)
    languages = Language.objects.all()
    visible_tests = problem.tests.all()[:problem.visible_tests_count]

    context = {
        'problem': problem,
        'languages': languages,
        'visible_tests': visible_tests,
    }

    return render(request, 'problems/problem_detail.html', context)


def problems_list(request):
    problems = Problem.objects.filter(contests__isnull=True)
    tags = ProblemTag.objects.all().order_by("name")
    problem_submissions = dict()
    
    search_query = request.GET.get("title", "").lower().strip().replace("ё", "е")
    selected_tag = request.GET.get("tag", "").strip()

    visible_contests = Contest.objects.filter(
        Q(hide_problems_until_start=False) | Q(start_time__lte=timezone.now())
    )
    visible_contest_problems = ContestProblem.objects.filter(contest__in=visible_contests)
    visible_problems_ids = visible_contest_problems.values_list("problem_id", flat=True)

    problems = (problems | Problem.objects.filter(id__in=visible_problems_ids)).distinct().order_by("title")

    if selected_tag:
        problems = problems.filter(tags__name=selected_tag)

    if request.user.is_authenticated:
        problems = problems.prefetch_related(
            Prefetch(
                "submission_set",
                queryset=Submission.objects.filter(user=request.user).order_by("-timestamp"),
                to_attr="user_submissions"
            )
        )
        
        for problem in problems:
            if hasattr(problem, "user_submissions") and problem.user_submissions:
                problem_submissions[problem.id] = problem.user_submissions[0]

    if search_query:
        problems = list(filter(lambda x: search_query in x.title.lower(), problems))

    context = {
        "problems": problems,
        "tags": tags,
        "problem_submissions": problem_submissions,
        "search_query": search_query,
        "selected_tag": selected_tag,
    }

    return render(request, "problems/problems_list.html", context)


def problem_submission_detail(request, submission_id):
    submission = get_object_or_404(Submission, id=submission_id)
    tests = submission.test_results.exclude(status=SubmissionStatus.StatusChoices.PENDING)
    is_checking = submission.status.status == SubmissionStatus.StatusChoices.PENDING

    context = {
        "submission": submission,
        "tests": tests,
        "is_checking": is_checking,
    }

    return render(request, "contests/submission_detail.html", context)


def problem_settings(request, problem_id):
    if not request.user.is_authenticated or not (request.user.is_admin() or request.user.is_teacher()):
        from django.http import HttpResponseForbidden
        return HttpResponseForbidden("Forbidden")
    
    problem = get_object_or_404(Problem, id=problem_id)
    tests = problem.fetch_tests

    if request.method == "POST":
        problem_form = ProblemForm(request.POST, instance=problem)
        test_form = TestForm()
        if problem_form.is_valid():
            problem_form.save()
    else:
        problem_form = ProblemForm(instance=problem)
        test_form = TestForm()

    context = {
        "problem": problem,
        "tests": tests,
        "problem_form" : problem_form,
        "test_form" : test_form,
    }

    return render(request, "problems/problem_settings.html", context)

@require_POST
def delete_problem_test(request, problem_id, test_id):
    if not request.user.is_authenticated or not (request.user.is_admin() or request.user.is_teacher()):
        return JsonResponse({'status': 'error', 'message': 'Forbidden'}, status=403)
    
    test = get_object_or_404(Test, id=test_id, problem_id=problem_id)
    test.delete()

    return JsonResponse({
        'status': 'success',
        'message': 'Тест удален',
        'test_id': test_id,
        'problem_id': problem_id
    })


@require_POST
def add_problem_test(request, problem_id):
    if not request.user.is_authenticated or not (request.user.is_admin() or request.user.is_teacher()):
        return JsonResponse({'status': 'error', 'message': 'Forbidden'}, status=403)
    
    problem = get_object_or_404(Problem, id=problem_id)
    form = TestForm(request.POST)

    if form.is_valid():
        test = form.save(commit=False)
        test.problem = problem
        test.save()
        return JsonResponse({
            'status': 'success',
            'test': {
                'id': test.id,
                'description': str(test)
            }
        })
    else:
        return JsonResponse({'status': 'error', 'message': 'Неверные данные теста', 'errors': form.errors}, status=400)

url = "http://server:2358/submissions"

def submit_to_judge0(submission):
    # url = "https://judge0-ce.p.rapidapi.com/submissions"
    headers = {
        "Content-Type": "application/json",
    }
    
    tests = submission.problem.fetch_tests()
    submission_tokens = list()
    for test in tests:
        payload = {
            "language_id": submission.language.language_id,
            "source_code": submission.content.content,
            "stdin": test.stdin,
            "expected_output": test.expected_output,
            "cpu_time_limit": submission.problem.time_limit,
            "memory_limit": submission.problem.memory_limit * 1024
        }
        response = requests.post(url, headers=headers, json=payload)

        if response.status_code == 201:
            submission_token = response.json()["token"]
            submission_tokens.append((test.id, submission_token))
        else:
            raise Exception(f"Failed to submit to Judge0. Response code: {str(response.status_code)}")
    return submission_tokens


def get_submission_result(submission_token):
    # url = f"https://judge0-ce.p.rapidapi.com/submissions/{submission_token}"
    headers = {
        "Accept": "application/json",
    }
    response = requests.get(f"{url}/{submission_token}", headers=headers)
    if response.status_code == 200:
        return response.json()
    else:
        if response.status_code == 400:
            return {
                "status": {
                    "id": 6,  # COMPILATION_ERROR
                    "description": "Compilation Error"
                }
            }
        raise Exception(f"Failed to get submission result. Response code: {str(response.status_code)}")


def update_submission_status(submission, tokens):
    failure_statuses = {
        4: SubmissionStatus.StatusChoices.WRONG_ANSWER,
        5: SubmissionStatus.StatusChoices.TIME_LIMIT_EXCEEDED,
        6: SubmissionStatus.StatusChoices.COMPILATION_ERROR,
        7: SubmissionStatus.StatusChoices.RUNTIME_ERROR,
        8: SubmissionStatus.StatusChoices.RUNTIME_ERROR,
        9: SubmissionStatus.StatusChoices.RUNTIME_ERROR,
        10: SubmissionStatus.StatusChoices.RUNTIME_ERROR,
        11: SubmissionStatus.StatusChoices.RUNTIME_ERROR,
        12: SubmissionStatus.StatusChoices.RUNTIME_ERROR,
        13: SubmissionStatus.StatusChoices.COMPILATION_ERROR,
        14: SubmissionStatus.StatusChoices.PRESENTATION_ERROR,
    }

    for test_id, token in tokens:
        try:
            result = get_submission_result(token)
            status_id = result["status"]["id"]

            while status_id == 1 or status_id == 2:
                result = get_submission_result(token)
                status_id = result["status"]["id"]

            test_result = SubmissionTestResult.objects.create(
                submission=submission,
                test_id=test_id,
                status=failure_statuses.get(status_id, SubmissionStatus.StatusChoices.ACCEPTED),
                execution_time=float(result.get("time")) * 1000 if result.get("time") != None else 0,
                memory_used=float(result.get("memory")) if result.get("memory") != None else 0,
                output=result.get("stdout", ""),
            )

            submission.execution_time = test_result.execution_time
            submission.memory_used = test_result.memory_used

            if test_result.memory_used > submission.problem.memory_limit * 1024:
                submission.status.status = SubmissionStatus.StatusChoices.MEMORY_LIMIT_EXCEEDED
                submission.status.save()
                submission.save()
                print(f"Updated submission {submission.id} status to {submission.status.status}")
                break

            if status_id in failure_statuses:
                submission.status.status = failure_statuses[status_id]
                submission.status.save()
                submission.save()
                print(f"Updated submission {submission.id} status to {submission.status.status}")
                break

            async_to_sync(get_channel_layer().group_send)(
                f"submission_{submission.id}",
                {
                    "type": "send_test_results",
                    "data": {
                        "test_id": test_id,
                        "test_status": test_result.status,
                        "test_execution_time": test_result.execution_time,
                        "test_memory_used": test_result.memory_used,
                    }
                }
            )
        except Exception as exception:
            print(f"Error while update submission status: {str(exception)}")
    else:
        submission.status.status = SubmissionStatus.StatusChoices.ACCEPTED
        submission.status.save()
        submission.save()
        print(f"All tests for submission {submission.id} passed. Status set to ACCEPTED")


@csrf_exempt
@api_view(["POST"])
def submit_code(request):
    data = request.data
    problem_id = data.get("problem_id")
    code = data.get("code")
    language_id = data.get("language_id")

    if not all([problem_id, code, language_id]):
        return Response(
            {"status": "error", "message": "Missing required fields"},
            status=status.HTTP_400_BAD_REQUEST,
        )

    submission_content = SubmissionContent.objects.create(content=code)
    submission_status = SubmissionStatus.objects.create(status=SubmissionStatus.StatusChoices.PENDING)
    language = Language.objects.get(language_id=language_id)

    submission = Submission.objects.create(
        user=request.user,
        problem_id=problem_id,
        language=language,
        content=submission_content,
        status=submission_status
    )

    try:
        tokens = submit_to_judge0(submission)
        update_submission_status(submission, tokens)
        return JsonResponse({"status": "success", "submission_id": submission.id})
    except Exception as exception:
        print(f"Error: {str(exception)} :(")
        return JsonResponse({"status": "error", "message": str(exception)})


def check_status(request):
    submission_id = request.GET.get("submission_id")
    submission = get_object_or_404(Submission, id=submission_id)
    return JsonResponse({"status": submission.status.status})
