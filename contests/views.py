from django.contrib.auth.decorators import login_required
from django.db.models.functions import Lower
from django.http import JsonResponse
from django.shortcuts import render, get_object_or_404, redirect
from django.views.decorators.csrf import csrf_exempt
from rest_framework import viewsets, status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from contests.models import Contest, ContestProblem, ContestParticipant, ContestSubmission, FavoriteContest
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
    search_query = request.GET.get("title", "").strip()
    show_favorites = request.GET.get("favorites", "").strip() == "true"

    contests = Contest.objects.all()
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
        contests = list(filter(lambda contest: search_query.lower() in contest.title.lower(), Contest.objects.all()))

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
    }

    return render(request, "contests/contests_list.html", context)


def contest_view(request, contest_id):
    return redirect("contest_problems", contest_id=contest_id)


def contest_problems(request, contest_id):
    contest = get_object_or_404(Contest, pk=contest_id)
    problems = ContestProblem.objects.filter(contest=contest)
    solved_problems = set()
    participant = None

    if request.user.is_authenticated:
        participant = ContestParticipant.objects.filter(contest=contest, user=request.user).first()
        if participant:
            accepted_submissions = ContestSubmission.objects.filter(
                participant=participant,
                contest_problem__in=problems,
                submission__status__status=SubmissionStatus.StatusChoices.ACCEPTED
            ).values_list('contest_problem__problem_id', flat=True)
            solved_problems = set(accepted_submissions)

    if not contest.is_started() and contest.hide_problems_until_start:
        problems = ContestProblem.objects.none()

    context = {
        "contest": contest,
        "problems": problems,
        "solved_problems": solved_problems,
        "participant": participant,
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

    context = {
        "contest": contest_submission.contest_problem.contest,
        "submission": submission,
        "tests": tests,
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
