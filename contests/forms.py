from django import forms

from contests.models import Contest, ContestProblem
from problems.models import Problem

class CreateContestForm(forms.ModelForm):

    class Meta:
        
        model = Contest
        fields = ["title", "description", "start_time", "end_time", "is_public", "hide_problems_until_start"]
        labels = {
            "title": "Название",
            "description": "Описание",
            "start_time": "Дата начала",
            "end_time": "Дата конца",
            "is_public": "Открытый",
            "hide_problems_until_start": "Скрыть задачи до начала",
        }
        widgets = {
            "start_time": forms.DateTimeInput(attrs={"class": "form-control", "type": "datetime-local"}, format="%Y-%m-%dT%H:%M"),
            "end_time": forms.DateTimeInput(attrs={"class": "form-control", "type": "datetime-local"}, format="%Y-%m-%dT%H:%M"),
        }


class ContestProblemForm(forms.ModelForm):

    class Meta:

        model = ContestProblem
        fields = ["problem"]
        labels = {
            "problem": "Задача",
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["problem"].queryset = Problem.objects.all()

ContestProblemFormSet = forms.inlineformset_factory(Contest, ContestProblem, form=ContestProblemForm, extra=1, can_delete=False)
