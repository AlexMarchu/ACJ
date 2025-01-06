from django.contrib import admin
from django import forms
from django_ckeditor_5.widgets import CKEditor5Widget

from problems.models import Test, Problem, ProblemTag, SubmissionStatus, SubmissionContent, Submission, Language, \
    SubmissionTestResult


class TestInline(admin.TabularInline):

    model = Test
    extra = 1


class ProblemAdminForm(forms.ModelForm):

    description = forms.CharField(widget=CKEditor5Widget(config_name='default'))

    class Meta:
        model = Problem
        fields = '__all__'


class ProblemAdmin(admin.ModelAdmin):
    
    form = ProblemAdminForm

    class Media:
        css = {
            'all': ('ckeditor/ckeditor5_admin.css',),
        }


admin.site.register(Test)
admin.site.register(SubmissionContent)
admin.site.register(Problem, ProblemAdmin)
admin.site.register(ProblemTag)
admin.site.register(SubmissionStatus)
admin.site.register(Submission)
admin.site.register(Language)
admin.site.register(SubmissionTestResult)
