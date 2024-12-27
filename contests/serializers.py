from rest_framework import serializers

from contests.models import Contest, ContestParticipant, ContestProblem, ContestSubmission
from problems.serializers import ProblemSerializer


class ContestProblemSerializer(serializers.ModelSerializer):
    problem = ProblemSerializer()

    class Meta:
        model = ContestProblem
        fields = ["id", "problem",]


class ContestSerializer(serializers.ModelSerializer):
    problems = ContestProblemSerializer(many=True, read_only=True)

    class Meta:
        model = Contest
        fields = ["id", "title", "start_time", "end_time", "is_public", "problems"]


class ContestParticipantSerializer(serializers.ModelSerializer):
    class Meta:
        model = ContestParticipant
        fields = ["id", "user", "contest", "joined_at"]


class ContestSubmissionSerializer(serializers.ModelSerializer):
    class Meta:
        model = ContestSubmission
        fields = ["id", "participant", "submission", "timestamp"]
