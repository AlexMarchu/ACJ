import requests
from django.http import JsonResponse
from django.shortcuts import get_object_or_404
from django.views.decorators.csrf import csrf_exempt
from rest_framework import viewsets, permissions, status
from rest_framework.decorators import api_view
from rest_framework.response import Response

from problems.models import SubmissionStatus, Language, Problem, Test, SubmissionContent, Submission
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
            "expected_output": test.expected_output
        }
        response = requests.post(url, headers=headers, json=payload)
        if response.status_code == 201:
            submission_token = response.json()["token"]
            submission_tokens.append(submission_token)
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
        raise Exception(f"Failed to get submission result. Response code: {str(response.status_code)}")


def update_submission_status(submission, tokens):
    all_passed = True
    for token in tokens:
        result = get_submission_result(token)
        if result["status"]["id"] != 3:
            all_passed = False
            break

    if all_passed:
        submission.status.status = SubmissionStatus.StatusChoices.ACCEPTED
    else:
        submission.status.status = SubmissionStatus.StatusChoices.REJECTED

    submission.status.save()


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
