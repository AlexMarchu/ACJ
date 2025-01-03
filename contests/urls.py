from django.urls import path

from contests.views import contests_list, contest_view, contest_problems, submit_contest_code, check_contest_status, \
    contest_problem_detail, join_contest, contest_submissions, contest_results, toggle_favorite_contest, \
    submission_detail

urlpatterns = [
    path('', contests_list, name='contests_list'),
    path('<int:contest_id>/', contest_view, name='contest'),
    path('<int:contest_id>/problems/', contest_problems, name='contest_problems'),
    path('<int:contest_id>/submissions/', contest_submissions, name='contest_submissions'),
    path('<int:contest_id>/submissions/<int:submission_id>', submission_detail, name='submission_detail'),
    path('<int:contest_id>/results/', contest_results, name='contest_results'),
    path('<int:contest_id>/join/', join_contest, name='join_contest'),
    path('<int:contest_id>/toggle_favorite/', toggle_favorite_contest, name='toggle_favorite_contest'),
    path('<int:contest_id>/problem/<int:problem_id>/', contest_problem_detail, name='contest_problem_detail'),
    path('<int:contest_id>/submit/<int:problem_id>/', submit_contest_code, name='submit_contest_code'),
    path('<int:contest_id>/status/<int:submission_id>/', check_contest_status, name='check_contest_status'),
]
