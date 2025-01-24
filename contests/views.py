from django.contrib.auth.decorators import login_required
from django.db.models.functions import Lower
from django.http import JsonResponse
from django.urls import reverse_lazy
from django.shortcuts import render, get_object_or_404, redirect
from django.views.decorators.csrf import csrf_exempt
from django.contrib.auth.mixins import UserPassesTestMixin
from django.views.generic import CreateView
from django.views.decorators.http import require_POST
from rest_framework import viewsets, status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from contests.models import Contest, ContestProblem, ContestParticipant, ContestSubmission, FavoriteContest
from contests.serializers import ContestSerializer, ContestProblemSerializer, ContestParticipantSerializer, \
    ContestSubmissionSerializer
from contests.forms import CreateContestForm, ContestProblemFormSet
from problems.models import Submission, SubmissionStatus, SubmissionContent, Language, Problem
from problems.views import submit_to_judge0, update_submission_status


class ContestViewSet(viewsets.ModelViewSet):

    queryset = Contest.objects.all()
    serializer_class = ContestSerializer


class ContestProblemViewSet(viewsets.ModelViewSet):

    queryset = ContestProblem.objects.all()
    serializer_class = ContestProblemSerializer


class ContestParticipantViewSet(viewsets.ModelViewSet):

    queryset = ContestParticipant.objects.all()
    serializer_class = ContestParticipantSerializer


class ContestSubmissionViewSet(viewsets.ModelViewSet):

    queryset = ContestSubmission.objects.all()
    serializer_class = ContestSubmissionSerializer


class CreateContestView(UserPassesTestMixin, CreateView):

    model = Contest
    form_class = CreateContestForm
    template_name = "contests/create_contest.html"
    success_url = reverse_lazy("home")

    def test_func(self):
        return self.request.user.is_teacher() or self.request.user.is_admin()

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        if self.request.POST:
            context['contest_problem_formset'] = ContestProblemFormSet(self.request.POST)
        else:
            context['contest_problem_formset'] = ContestProblemFormSet()
        context['problems'] = Problem.objects.all()
        return context

    def form_valid(self, form):
        context = self.get_context_data()
        contest_problem_formset = context['contest_problem_formset']
        if contest_problem_formset.is_valid():
            self.object = form.save()
            contest_problem_formset.instance = self.object
            contest_problem_formset.save()
            return super().form_valid(form)
        else:
            return self.form_invalid(form)


def contests_list(request):
    contests_data = list()
    search_query = request.GET.get("title", "").lower().strip().replace("ё", "е")
    show_favorites = request.GET.get("favorites", "").strip() == "true"

    contests = Contest.objects.all().order_by("-start_time")
    favorite_contests = set()

    if request.user.is_authenticated:
        favorite_contests = FavoriteContest.objects.filter(user=request.user).values_list("contest", flat=True)
        if show_favorites:
            contests = contests.filter(id__in=favorite_contests)
        favorite_contests = set(favorite_contests)

    if search_query:
        # this doesn't works so now we have O(N) search by contest titles
        # contests = Contest.objects.annotate(lower_title=Lower('title'))
        # .filter(lower_title__icontains=search_query.lower())
        contests = list(filter(lambda contest: search_query in contest.title.lower(), contests))

    for contest in contests:
        participant = None
        if request.user.is_authenticated:
            participant = ContestParticipant.objects.filter(contest=contest, user=request.user).first()
            if not contest.is_public and not (request.user.is_admin() or request.user.is_teacher()):
                continue
        elif not contest.is_public:
            continue

        contests_data.append((contest, participant))

    context = {
        "contests_data": contests_data,
        "search_query": search_query,
        "favorite_contests": favorite_contests,
        "show_favorites": show_favorites,
    }

    return render(request, "contests/contests_list.html", context)


def contest_view(request, contest_id):
    return redirect("contest_problems", contest_id=contest_id)


def contest_problems(request, contest_id):
    contest = get_object_or_404(Contest, pk=contest_id)
    problems = ContestProblem.objects.filter(contest=contest)
    problem_statuses = dict()  # problem_id: (status, submission_id)
    participant = None
    is_favorite = False
    have_permission = contest.is_public

    if request.user.is_authenticated:
        is_favorite = FavoriteContest.objects.filter(user=request.user, contest=contest).exists()
        participant = ContestParticipant.objects.filter(contest=contest, user=request.user).first()
        if participant:
            submissions = ContestSubmission.objects.filter(
                participant=participant,
                contest_problem__in=problems,
            ).select_related(
                "submission__status",
                "contest_problem",
            ).order_by("-timestamp")

            for submission in submissions:
                problem_id = submission.contest_problem.get_id()
                if problem_id not in problem_statuses:
                    problem_statuses[problem_id] = (
                        submission.get_submission_status(),
                        submission.submission.id
                    )
        if not contest.is_public:
            have_permission = not request.user.is_student() or participant

    if not contest.is_started() and contest.hide_problems_until_start:
        problems = ContestProblem.objects.none()

    context = {
        "contest": contest,
        "problems": problems,
        "problem_statuses": problem_statuses,
        "participant": participant,
        "is_favorite": is_favorite,
        "have_permission": have_permission,
    }

    return render(request, "contests/contest_problems.html", context)


def contest_problem_detail(request, contest_id, problem_id):
    contest = get_object_or_404(Contest, id=contest_id)
    contest_problem = get_object_or_404(ContestProblem, contest=contest, problem_id=problem_id)
    problem = contest_problem.problem
    languages = Language.objects.all()
    visible_tests = problem.tests.all()[:problem.visible_tests_count]

    participant = None
    if request.user.is_authenticated:
        participant = ContestParticipant.objects.filter(contest=contest, user=request.user).first()

    context = {
        "contest": contest,
        "problem": problem,
        "languages": languages,
        "visible_tests": visible_tests,
        "participant": participant,
        "problem_letter": contest_problem.letter,
    }

    return render(request, "problems/problem_detail.html", context)


@login_required(login_url="/auth/login/")
def contest_submissions(request, contest_id):
    contest = get_object_or_404(Contest, id=contest_id)
    user = request.user

    submissions = ContestSubmission.objects.filter(
        participant__contest=contest,
        participant__user=user,
    ).select_related("submission", "contest_problem", "submission__language", "submission__status").order_by("-timestamp")

    context = {
        "contest": contest,
        "submissions": submissions,
        "is_favorite": FavoriteContest.objects.filter(user=request.user, contest=contest).exists(),
    }

    return render(request, "contests/contest_submissions.html", context)


def contest_results(request, contest_id):
    contest = get_object_or_404(Contest, id=contest_id)
    participants = ContestParticipant.objects.filter(contest=contest).select_related("user")
    problems = ContestProblem.objects.filter(contest=contest).order_by("letter")

    hide_virtual = request.GET.get("hide_virtual", "true").lower() == "true"
    hide_official = request.GET.get("hide_official", "false").lower() == "true"

    if hide_virtual:
        participants = participants.filter(is_virtual=False)
    if hide_official:
        participants = participants.filter(is_virtual=True)

    results = list()
    for participant in participants:
        row_data = {
            "participant": participant,
            "status": participant.is_virtual,
            "problems": dict(),
            "solved_count": 0,
        }

        for problem in problems:
            submissions = ContestSubmission.objects.filter(
                participant=participant,
                contest_problem=problem,
            ).select_related("submission__status").order_by("timestamp")

            submissions_count = submissions.count()
            accepted_submission_number = None

            for number, submission in enumerate(submissions, start=1):
                if (submission.submission.status.status == SubmissionStatus.StatusChoices.ACCEPTED):
                    accepted_submission_number = number
                    break

            if accepted_submission_number is not None:
                row_data["problems"][problem.letter] = f"+{accepted_submission_number if accepted_submission_number != 1 else ''}"
                row_data["solved_count"] += 1
            else:
                row_data["problems"][problem.letter] = f"-{submissions_count}" if submissions_count else "."

        results.append(row_data)

    results.sort(key=lambda x: x["solved_count"], reverse=True)
    for number, result in enumerate(results, start=1):
        result["place"] = number

    context = {
        "contest": contest,
        "problems": problems,
        "results": results,
        "is_favorite": FavoriteContest.objects.filter(user=request.user, contest=contest).exists(),
        "hide_virtual": hide_virtual,
        "hide_official": hide_official,
    }

    return render(request, "contests/contest_results.html", context)


def contest_settings(request, contest_id):
    if not request.user.is_authenticated or not (request.user.is_admin() or request.user.is_teacher()):
        from django.http import HttpResponseForbidden
        return HttpResponseForbidden("Forbidden")

    contest = get_object_or_404(Contest, id=contest_id)

    contest_problems = ContestProblem.objects.filter(contest=contest).select_related("problem").order_by(
        "problem__title")
    contest_problem_ids = set(map(lambda x: x.problem.id, contest_problems))
    all_problems = Problem.objects.all().order_by("title")

    for problem in all_problems:
        problem.in_contest = problem.id in contest_problem_ids

    if request.method == "POST":
        contest_form = CreateContestForm(request.POST, instance=contest)
        if contest_form.is_valid():
            contest_form.save()
    else:
        contest_form = CreateContestForm(instance=contest)

    return render(request, "contests/contest_settings.html", {
        "contest": contest,
        "contest_form": contest_form,
        "all_problems": sorted(all_problems, key=lambda x: not x.in_contest),
    })


@require_POST
def add_contest_problem(request, contest_id, problem_id):
    contest = get_object_or_404(Contest, id=contest_id)
    problem = get_object_or_404(Problem, id=problem_id)

    if not ContestProblem.objects.filter(contest=contest, problem=problem).exists():
        ContestProblem.objects.create(contest=contest, problem=problem)
        problem.in_contest = True
        return JsonResponse(
            {
                "status": "success",
                "message": "Задача добавлена",
                "problem_id": problem.id,
                "contest_id": contest_id,
                "in_contest": problem.in_contest,
            }
        )
    return JsonResponse(
        {
            "status": "error",
            "message": "Задача уже добавлена",
            "problem_id": problem.id,
            "contest_id": contest_id,
            "in_contest": False,
        }, status=400
    )


@require_POST
def delete_contest_problem(request, contest_id, problem_id):
    contest = get_object_or_404(Contest, id=contest_id)
    problem = get_object_or_404(Problem, id=problem_id)

    contest_problem = ContestProblem.objects.filter(contest=contest, problem=problem).first()

    if contest_problem:
        contest_problem.delete()
        return JsonResponse(
            {
                "status": "success",
                "message": "Задача удалена",
                "problem_id": problem.id,
                "contest_id": contest.id,
            }
        )
    return JsonResponse(
        {
            "status": "error",
            "message": "Задачи нет в турнире",
            "problem_id": problem.id,
            "contest_id": contest.id,
        }
    )


@login_required(login_url="/auth/login/")
def join_contest(request, contest_id):
    contest = get_object_or_404(Contest, id=contest_id)
    contest_participant, created = ContestParticipant.objects.get_or_create(
        contest=contest,
        user=request.user,
        defaults={'is_virtual': contest.is_finished()}
    )

    return redirect("contest", contest_id=contest_id)


@api_view(["POST"])
@permission_classes([IsAuthenticated])
@csrf_exempt
def toggle_favorite_contest(request, contest_id):
    contest = get_object_or_404(Contest, id=contest_id)
    favorite, created = FavoriteContest.objects.get_or_create(user=request.user, contest=contest)
    if not created:
        favorite.delete()
        return JsonResponse({"status": "deleted"}, status=status.HTTP_200_OK)
    return JsonResponse({"status": "created"}, status=status.HTTP_201_CREATED)


@login_required(login_url="/auth/login")
def submission_detail(request, contest_id, submission_id):
    contest_submission = get_object_or_404(ContestSubmission, submission_id=submission_id,
                                           participant__contest_id=contest_id)
    submission = contest_submission.submission
    tests = submission.test_results.exclude(status=SubmissionStatus.StatusChoices.PENDING)
    is_checking = submission.status.status == SubmissionStatus.StatusChoices.PENDING

    context = {
        "contest": contest_submission.contest_problem.contest,
        "submission": submission,
        "tests": tests,
        "is_checking": is_checking,
    }

    return render(request, "contests/submission_detail.html", context)


@api_view(["POST"])
def submit_contest_code(request, contest_id, problem_id):
    contest = get_object_or_404(Contest, id=contest_id)
    contest_problem = get_object_or_404(ContestProblem, contest=contest, problem_id=problem_id)
    participant = get_object_or_404(ContestParticipant, contest=contest, user=request.user)

    data = request.data
    code = data.get("code")
    language_id = data.get("language_id")

    if not all([code, language_id]):
        return Response(
            {"status": "error", "message": "Missing required fields"},
            status=status.HTTP_400_BAD_REQUEST
        )

    submission_content = SubmissionContent.objects.create(content=code)
    submission_status = SubmissionStatus.objects.create(status=SubmissionStatus.StatusChoices.PENDING)
    language = Language.objects.get(language_id=language_id)

    submission = Submission.objects.create(
        user=request.user,
        problem=contest_problem.problem,
        language=language,
        content=submission_content,
        status=submission_status
    )

    contest_submission = ContestSubmission.objects.create(
        participant=participant,
        contest_problem=contest_problem,
        submission=submission
    )

    try:
        tokens = submit_to_judge0(submission)
        update_submission_status(submission, tokens)
        return JsonResponse({"status": "success", "submission_id": submission.id})
    except Exception as exception:
        print(f"Error: {str(exception)} :(")
        return JsonResponse({"status": "error", "message": str(exception)})


def check_contest_status(request, contest_id, submission_id):
    submission = get_object_or_404(ContestSubmission, submission_id=submission_id, participant__contest_id=contest_id)
    return JsonResponse({"status": submission.submission.status.status})
