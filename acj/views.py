from django.contrib.auth.decorators import login_required
from django.shortcuts import render, get_object_or_404

from problems.models import Problem, Language


@login_required(login_url='/auth/login/')
def home_view(request):
    return render(request, 'content_base.html')


@login_required(login_url='/auth/login/')
def problem_list(request):
    problems = Problem.objects.all()
    return render(request, 'problems/problem_list.html', {'problems': problems})


def problem_detail(request, problem_id):
    problem = get_object_or_404(Problem, id=problem_id)
    languages = Language.objects.all()
    context = {
        'problem': problem,
        'languages': languages,
    }
    return render(request, 'problems/problem_detail.html', context)