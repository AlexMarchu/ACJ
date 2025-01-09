from django import forms
from django_ckeditor_5.widgets import CKEditor5Widget

from problems.models import Problem, Test


class ProblemForm(forms.ModelForm):

    class Meta:
        model = Problem
        fields = ["title", "description", "input_format", "output_format", "time_limit", "memory_limit", "tags"]
        labels = {
            "title": "Название",
            "description": "Условие",
            "input_format": "Формат входных данных",
            "output_format": "Формат выходных данных",
            "time_limit": "Ограничение по времени",
            "memory_limit": "Ограничение по памяти",
            "tags": "Тэги",
        }
        widgets = {
            'title': forms.TextInput(attrs={'class': 'form-control'}),
            'description': CKEditor5Widget(config_name='extends'),
            'input_format': forms.TextInput(attrs={'class': 'form-control'}),
            'output_format': forms.TextInput(attrs={'class': 'form-control'}),
            'time_limit': forms.TextInput(attrs={'class': 'form-control'}),
            'memory_limit': forms.TextInput(attrs={'class': 'form-control'}),
        }


class TestForm(forms.ModelForm):

    class Meta:
        model = Test
        fields = ["stdin", "expected_output"]
        labels = {
            "stdin": "Входные данные",
            "expected_output": "Ожидаемый результат",
        }

TestFormSet = forms.inlineformset_factory(Problem, Test, form=TestForm, extra=1, can_delete=False)
