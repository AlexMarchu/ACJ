from django.db import models
from django.utils import timezone

from users.models import ACJUser
from problems.models import Problem, Submission


class Contest(models.Model):
    title = models.CharField(max_length=150)
    start_time = models.DateTimeField(default=timezone.now)
    end_time = models.DateTimeField()
    is_public = models.BooleanField(default=True)
    participants = models.ManyToManyField(ACJUser, related_name='contests', through='ContestParticipant')

    def __str__(self):
        return self.title

    def is_active(self):
        now = timezone.now()
        return self.start_time <= now <= self.end_time


class ContestParticipant(models.Model):
    contest = models.ForeignKey(Contest, on_delete=models.CASCADE, related_name='participants_info')
    user = models.ForeignKey(ACJUser, on_delete=models.CASCADE, related_name='contests_participations')
    joined_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.contest} - {self.user}"


class ContestProblem(models.Model):
    contest = models.ForeignKey(Contest, on_delete=models.CASCADE, related_name='problems')
    problem = models.ForeignKey(Problem, on_delete=models.CASCADE, related_name='contests')

    def __str__(self):
        return f"{self.contest} - {self.problem}"


class ContestSubmission(models.Model):
    participant = models.ForeignKey(ContestParticipant, on_delete=models.CASCADE, related_name='submissions')
    submission = models.ForeignKey(Submission, on_delete=models.CASCADE, related_name='contest_submissions')
    timestamp = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"ContestSubmission by {self.participant} in {self.participant.contest}"
