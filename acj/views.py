from django.contrib.auth.decorators import login_required
from django.shortcuts import render, get_object_or_404, redirect

from problems.models import Problem, Language


@login_required(login_url='/auth/login/')
def home_view(request):
    # TODO: add homepage
    # return render(request, 'content_base.html')
    return redirect("contest_list")


@login_required(login_url='/auth/login/')
def problem_list(request):
    problems = Problem.objects.all()
    return render(request, 'problems/problem_list.html', {'problems': problems})


def problem_detail(request, problem_id):
    problem = get_object_or_404(Problem, id=problem_id)
    languages = Language.objects.all()
    visible_tests = problem.tests.all()[:problem.visible_tests_count]

    context = {
        'problem': problem,
        'languages': languages,
        'visible_tests': visible_tests,
    }

    return render(request, 'problems/problem_detail.html', context)
