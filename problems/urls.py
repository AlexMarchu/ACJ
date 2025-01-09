from django.urls import path, include
from rest_framework.routers import DefaultRouter

from problems.views import ProblemViewSet, TestViewSet, CreateProblemView, submit_code, check_status
from contests.views import ContestViewSet, ContestParticipantViewSet, ContestSubmissionViewSet, ContestProblemViewSet, CreateContestView

router = DefaultRouter()
router.register(r'problems', ProblemViewSet)
router.register(r'tests', TestViewSet)

router.register(r'contests', ContestViewSet)
router.register(r'contest-problems', ContestProblemViewSet)
router.register(r'contest-participants', ContestParticipantViewSet)
router.register(r'contest-submissions', ContestSubmissionViewSet)

urlpatterns = [
    path('', include(router.urls)),
    path('submit_code/', submit_code, name='submit_code'),
    path('check_status/', check_status, name='check_status'),
    path('create_problem', CreateProblemView.as_view(), name='create_problem'),
    path('create_contest', CreateContestView.as_view(), name='create_contest'),
]
