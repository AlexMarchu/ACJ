from django.contrib import admin

from problems.models import Test, Problem, ProblemTag, SubmissionStatus, SubmissionContent, Submission, Language

admin.site.register(Test)
admin.site.register(SubmissionContent)
admin.site.register(Problem)
admin.site.register(ProblemTag)
admin.site.register(SubmissionStatus)
admin.site.register(Submission)
admin.site.register(Language)
