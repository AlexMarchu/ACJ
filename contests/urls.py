from django.urls import path, include
from rest_framework.routers import DefaultRouter

from contests.views import ContestViewSet, ContestParticipantViewSet, ContestSubmissionViewSet, ContestProblemViewSet

router = DefaultRouter()
router.register(r'contests', ContestViewSet)
router.register(r'contest-problems', ContestProblemViewSet)
router.register(r'contest-participants', ContestParticipantViewSet)
router.register(r'contest-submissions', ContestSubmissionViewSet)

urlpatterns = [
    path('', include(router.urls)),
]