from django.contrib import admin

from problems.models import Test, Problem, ProblemTag, SubmissionStatus, SubmissionContent, Submission, Language


class TestInline(admin.TabularInline):
    model = Test
    extra = 1


class ProblemAdmin(admin.ModelAdmin):
    list_display = ('id', 'title', 'author')
    filter_horizontal = ('tags',)
    inlines = [TestInline]


admin.site.register(Test)
admin.site.register(SubmissionContent)
admin.site.register(Problem, ProblemAdmin)
admin.site.register(ProblemTag)
admin.site.register(SubmissionStatus)
admin.site.register(Submission)
admin.site.register(Language)
