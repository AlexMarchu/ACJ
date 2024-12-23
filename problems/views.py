import requests

from problems.models import SubmissionStatus, Language


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
    for token in tokens:
        result = get_submission_result(token)
        if result["status"]["id"] == 3:
            submission.status.status = SubmissionStatus.StatusChoices.ACCEPTED
        else:
            submission.status.status = SubmissionStatus.StatusChoices.REJECTED
        submission.status.save()
