from django.http import JsonResponse
from django.shortcuts import render, get_object_or_404
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
    context = {
        "contests": Contest.objects.all(),
    }
    return render(request, "contests/contests.html", context)


def contest_detail(request, contest_id):
    contest = get_object_or_404(Contest, pk=contest_id)
    contest_problems = ContestProblem.objects.filter(contest=contest)
    solved_problems = set()

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
    }

    return render(request, "contests/contest_detail.html", context)


def contest_problem_detail(request, contest_id, problem_id):
    contest = get_object_or_404(Contest, id=contest_id)
    contest_problem = get_object_or_404(ContestProblem, contest=contest, problem_id=problem_id)
    problem = contest_problem.problem
    languages = Language.objects.all()
    visible_tests = problem.tests.all()[:problem.visible_tests_count]

    context = {
        "contest": contest,
        "problem": problem,
        "languages": languages,
        "visible_tests": visible_tests,
    }

    return render(request, "problems/problem_detail.html", context)


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
