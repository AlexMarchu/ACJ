from django.urls import path, include
from rest_framework.routers import DefaultRouter

from problems.views import ProblemViewSet, TestViewSet

router = DefaultRouter()
router.register(r'problems', ProblemViewSet)
router.register(r'tests', TestViewSet)

urlpatterns = [
    path('', include(router.urls)),
]
