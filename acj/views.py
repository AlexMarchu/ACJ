from django.contrib.auth.decorators import login_required
from django.shortcuts import render, get_object_or_404, redirect

from problems.models import Problem, Language


def home_view(request):
    return redirect("contests_list")
