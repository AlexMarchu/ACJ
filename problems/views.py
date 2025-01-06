import requests
from django.http import JsonResponse
from django.shortcuts import get_object_or_404, render
from django.views.decorators.csrf import csrf_exempt
from django.db.models import Q
from django.utils import timezone
from rest_framework import viewsets, permissions, status
from rest_framework.decorators import api_view
from rest_framework.response import Response
from channels.layers import get_channel_layer
from asgiref.sync import async_to_sync

from contests.models import Contest, ContestProblem
from problems.models import SubmissionStatus, Language, Problem, Test, SubmissionContent, Submission, \
    SubmissionTestResult
from problems.permissions import IsAdminOrTeacher
from problems.serializers import ProblemSerializer, TestSerializer


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


def problem_list(request):
    queryset = Problem.objects.filter(contests__isnull=True)

    visible_contests = Contest.objects.filter(
        Q(hide_problems_until_start=False) | Q(start_time__lte=timezone.now())
    )
    visible_contest_problems = ContestProblem.objects.filter(contest__in=visible_contests)
    visible_problems_ids = visible_contest_problems.values_list("problem_id", flat=True)

    queryset = queryset | Problem.objects.filter(id__in=visible_problems_ids)

    context = {
        "problems": list(queryset),
    }

    return render(request, "problems/problem_list.html", context)


def submit_to_judge0(submission):
    url = "https://judge0-ce.p.rapidapi.com/submissions"
    headers = {
        "Accept": "application/json",
        "Content-Type": "application/json",
        "x-rapidapi-key": "fc3f3f5b5cmsh85267e1e76be9bap12876ajsnb49bd475f152",
        "x-rapidapi-host": "judge0-ce.p.rapidapi.com",
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
    url = f"https://judge0-ce.p.rapidapi.com/submissions/{submission_token}"
    headers = {
        "Accept": "application/json",
        "x-rapidapi-key": "fc3f3f5b5cmsh85267e1e76be9bap12876ajsnb49bd475f152",
        "x-rapidapi-host": "judge0-ce.p.rapidapi.com",
    }
    response = requests.get(url, headers=headers)
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

            test_result = SubmissionTestResult.objects.create(
                submission=submission,
                test_id=test_id,
                status=failure_statuses.get(status_id, SubmissionStatus.StatusChoices.ACCEPTED),
                execution_time=float(result.get("time", 0)) * 1000,
                memory_used=float(result.get("memory", 0)),
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
