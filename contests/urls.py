from django.urls import path

from contests.views import contests_list, contest_detail, submit_contest_code, check_contest_status, \
    contest_problem_detail

urlpatterns = [
    path('', contests_list, name='contest_list'),
    path('<int:contest_id>/', contest_detail, name='contest_detail'),
    path('<int:contest_id>/problem/<int:problem_id>/', contest_problem_detail, name='contest_problem_detail'),
    path('<int:contest_id>/submit/<int:problem_id>/', submit_contest_code, name='submit_contest_code'),
    path('<int:contest_id>/status/<int:submission_id>/', check_contest_status, name='check_contest_status'),
]
