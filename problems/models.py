from django.db import models
from django.contrib.auth import get_user_model

User = get_user_model()


class ProblemTag(models.Model):
    name = models.CharField(max_length=128)


class Problem(models.Model):
    title = models.CharField(max_length=255)
    author = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name="problems")
    description = models.TextField()
    input_format = models.TextField()
    output_format = models.TextField()
    time_limit = models.IntegerField(default=1)
    memory_limit = models.IntegerField(default=256)
    tags = models.ManyToManyField(ProblemTag)

    def __str__(self):
        return f"{self.title}"

    def fetch_tests(self):
        return Test.objects.filter(problem=self)


class Test(models.Model):
    problem = models.ForeignKey(Problem, on_delete=models.CASCADE)
    stdin = models.TextField()
    expected_output = models.TextField()


class Language(models.Model):
    name = models.CharField(max_length=128, unique=True)
    language_id = models.IntegerField(unique=True)

    def __str__(self):
        return f"{self.name} (ID: {self.language_id})"


class SubmissionContent(models.Model):
    content = models.TextField(verbose_name="Код")


class SubmissionStatus(models.Model):
    class StatusChoices(models.TextChoices):
        PENDING = "NP", "PENDING"
        ACCEPTED = "OK", "ACCEPTED"
        REJECTED = "RJ", "REJECTED"
        COMPILATION_ERROR = "CE", "COMPILATION_ERROR"
        RUNTIME_ERROR = "RE", "RUNTIME_ERROR"
        PRESENTATION_ERROR = "PE", "PRESENTATION_ERROR"
        WRONG_ANSWER = "WA", "WRONG_ANSWER"
        TIME_LIMIT_EXCEEDED = "TL", "TIME_LIMIT_EXCEEDED"
        MEMORY_LIMIT_EXCEEDED = "ML", "MEMORY_LIMIT_EXCEEDED"
        AWAITING_MANUAL = "AW", "AWAITING_MANUAL"
        REJECTED_MANUAL = "RM", "REJECTED_MANUAL"
        BANNED = "BA", "BANNED"

    status = models.CharField(choices=StatusChoices.choices, default=StatusChoices.PENDING, max_length=3)


class Submission(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    problem = models.ForeignKey(Problem, on_delete=models.CASCADE)
    language = models.ForeignKey(Language, on_delete=models.CASCADE)
    timestamp = models.DateTimeField(auto_now_add=True)
    execution_time = models.FloatField(null=True, blank=True)
    memory_used = models.FloatField(null=True, blank=True)
    content = models.ForeignKey(SubmissionContent, on_delete=models.CASCADE)
    status = models.ForeignKey(SubmissionStatus, on_delete=models.CASCADE)

    def __str__(self):
        return f"Submission by {self.user.username} for {self.problem.title}"
