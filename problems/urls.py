from django.urls import path, include
from rest_framework.routers import DefaultRouter

from problems.views import ProblemViewSet, TestViewSet, submit_code, check_status

router = DefaultRouter()
router.register(r'problems', ProblemViewSet)
router.register(r'tests', TestViewSet)

urlpatterns = [
    path('', include(router.urls)),
    path('submit_code/', submit_code, name='submit_code'),
    path('check_status/', check_status, name='check_status'),
]
