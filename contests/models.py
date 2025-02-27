from django.db import models
from django.utils import timezone

from users.models import ACJUser
from problems.models import Problem, Submission


class Contest(models.Model):

    title = models.CharField(max_length=150)
    description = models.TextField(null=True, blank=True)
    start_time = models.DateTimeField(default=timezone.now)
    end_time = models.DateTimeField()
    is_public = models.BooleanField(default=True)
    participants = models.ManyToManyField(ACJUser, related_name='contests', through='ContestParticipant')
    hide_problems_until_start = models.BooleanField(default=False)

    def __str__(self):
        return self.title

    def is_started(self):
        return timezone.now() >= self.start_time

    def is_active(self):
        return self.start_time <= timezone.now() <= self.end_time

    def is_finished(self):
        return timezone.now() >= self.end_time
    
    def get_problems_count(self):
        return self.problems.count()


class ContestParticipant(models.Model):

    contest = models.ForeignKey(Contest, on_delete=models.CASCADE, related_name='participants_info')
    user = models.ForeignKey(ACJUser, on_delete=models.CASCADE, related_name='contests_participations')
    joined_at = models.DateTimeField(auto_now_add=True)
    is_virtual = models.BooleanField(default=False)

    def __str__(self):
        return f"{self.contest} - {self.user}"
    
    def get_status(self):
        return ["офиц.", "внек."][self.is_virtual]
    
    def get_contest_id(self):
        return self.contest.id

    def get_solved_problems_count(self):
        from problems.models import SubmissionStatus
        return sum(ContestSubmission.objects.filter(
            participant=self,
            contest_problem=problem,
            submission__status__status=SubmissionStatus.StatusChoices.ACCEPTED
        ).exists() for problem in self.contest.problems.all())


class ContestProblem(models.Model):

    contest = models.ForeignKey(Contest, on_delete=models.CASCADE, related_name='problems')
    problem = models.ForeignKey(Problem, on_delete=models.CASCADE, related_name='contests')
    letter = models.CharField(max_length=3, blank=True, null=True)

    class Meta:

        constraints = [
            models.UniqueConstraint(
                fields=["contest", "problem"],
                name="unique_contest_problem"
            )
        ]

    def save(self, *args, **kwargs):
        if not self.letter:
            problem_count = ContestProblem.objects.filter(contest=self.contest).count()
            letter = chr(ord('A') + problem_count % 26)
            number = problem_count // 26
            self.letter = letter if number == 0 else f"{letter}{number}"
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.contest} - {self.problem}"

    def get_id(self):
        return self.problem.id

    def get_title(self):
        return self.problem.title

    def get_description(self):
        return self.problem.description

    def get_memory_limit(self):
        return self.problem.memory_limit

    def get_time_limit(self):
        return self.problem.time_limit

    def is_visible(self):
        return self.contest.is_active() or not self.contest.hide_problems_until_start


class ContestSubmission(models.Model):

    participant = models.ForeignKey(ContestParticipant, on_delete=models.CASCADE, related_name='submissions')
    contest_problem = models.ForeignKey(ContestProblem, on_delete=models.CASCADE, related_name='submissions', default=1)
    submission = models.ForeignKey(Submission, on_delete=models.CASCADE, related_name='contest_submissions')
    timestamp = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"ContestSubmission by {self.participant} in {self.participant.contest}"
    
    def get_participant_username(self):
        return self.participant.user.username
    
    def get_participant_name(self):
        return self.participant.user.get_name()
    
    def get_contest_id(self):
        return self.contest_problem.contest.id
    
    def get_problem_id(self):
        return self.contest_problem.problem.id
    
    def get_submission_id(self):
        return self.submission.id
    
    def get_submission_status(self):
        return self.submission.status.status


class FavoriteContest(models.Model):
    
    user = models.ForeignKey(ACJUser, on_delete=models.CASCADE, related_name='favorite_contests')
    contest = models.ForeignKey(Contest, on_delete=models.CASCADE, related_name='favorited_by')

    def __str__(self):
        return f"{self.user.username} — {self.contest.title}"
