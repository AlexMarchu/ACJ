from rest_framework import viewsets
from contests.models import Contest, ContestProblem, ContestParticipant, ContestSubmission
from contests.serializers import ContestSerializer, ContestProblemSerializer, ContestParticipantSerializer, \
    ContestSubmissionSerializer


class ContestViewSet(viewsets.ModelViewSet):
    queryset = Contest.objects.all()
    serializer_class = ContestSerializer


class ContestProblemViewSet(viewsets.ModelViewSet):
    queryset = ContestProblem.objects.all()
    serializer_class = ContestProblemSerializer


class ContestParticipantViewSet(viewsets.ModelViewSet):
    queryset = ContestParticipant.objects.all()
    serializer_class = ContestParticipantSerializer


class ContestSubmissionViewSet(viewsets.ModelViewSet):
    queryset = ContestSubmission.objects.all()
    serializer_class = ContestSubmissionSerializer
