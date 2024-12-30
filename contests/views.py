from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.shortcuts import render, get_object_or_404, redirect
from rest_framework import viewsets, status
from rest_framework.decorators import api_view
from rest_framework.response import Response

from contests.models import Contest, ContestProblem, ContestParticipant, ContestSubmission
from contests.serializers import ContestSerializer, ContestProblemSerializer, ContestParticipantSerializer, \
    ContestSubmissionSerializer
from problems.models import Submission, SubmissionStatus, SubmissionContent, Language
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


def contests_list(request):
    contests_data = list()

    for contest in Contest.objects.all():
        participant = None
        if request.user.is_authenticated:
            participant = ContestParticipant.objects.filter(contest=contest, user=request.user).first()
        contests_data.append((contest, participant))

    context = {
        "contests_data": contests_data,
    }

    return render(request, "contests/contests.html", context)


def contest_detail(request, contest_id):
    contest = get_object_or_404(Contest, pk=contest_id)
    contest_problems = ContestProblem.objects.filter(contest=contest)
    solved_problems = set()
    participant = None

    if request.user.is_authenticated:
        participant = ContestParticipant.objects.filter(contest=contest, user=request.user).first()
        if participant:
            accepted_submissions = ContestSubmission.objects.filter(
                participant=participant,
                contest_problem__in=contest_problems,
                submission__status__status=SubmissionStatus.StatusChoices.ACCEPTED
            ).values_list('contest_problem__problem_id', flat=True)
            solved_problems = set(accepted_submissions)

    context = {
        "contest": contest,
        "contest_problems": contest_problems,
        "solved_problems": solved_problems,
        "participant": participant,
    }

    return render(request, "contests/contest_detail.html", context)


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
    ).select_related("submission", "contest_problem", "submission__language", "submission__status")

    context = {
        "contest": contest,
        "submissions": submissions,
    }

    return render(request, "contests/contest_submissions.html", context)


def contest_results(request, contest_id):
    contest = get_object_or_404(Contest, id=contest_id)
    participants = ContestParticipant.objects.filter(contest=contest).select_related("user")
    problems = ContestProblem.objects.filter(contest=contest).order_by("letter")

    results = list()
    for participant in participants:
        row_data = {
            "user": participant.user,
            "status": participant.is_virtual,
            "problems": dict(),
            "solved_count": 0,
        }
        for problem in problems:
            submissions = ContestSubmission.objects.filter(
                participant=participant,
                contest_problem=problem,
            ).select_related("submission__status")
            if submissions.exists():
                row_data["problems"][problem.letter] = "+" if any(
                    submission.submission.status.status == SubmissionStatus.StatusChoices.ACCEPTED for submission in
                    submissions) else "-"
            else:
                row_data["problems"][problem.letter] = "."
        row_data["solved_count"] = list(row_data["problems"].values()).count("+")
        results.append(row_data)

    results.sort(key=lambda x: x["solved_count"], reverse=True)
    for index, result in enumerate(results):
        result["place"] = index + 1

    context = {
        "contest": contest,
        "problems": problems,
        "results": results,
    }

    return render(request, "contests/contest_results.html", context)


@login_required(login_url="/auth/login/")
def join_contest(request, contest_id):
    contest = get_object_or_404(Contest, id=contest_id)
    contest_participant, created = ContestParticipant.objects.get_or_create(
        contest=contest,
        user=request.user,
        defaults={'is_virtual': not contest.is_active()}
    )

    return redirect("contest_detail", contest_id=contest_id)


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
