from rest_framework import serializers

from problems.models import Problem, Test, ProblemTag


class ProblemTagSerializer(serializers.ModelSerializer):

    class Meta:
        model = ProblemTag
        fields = ["id", "name"]


class TestSerializer(serializers.ModelSerializer):

    class Meta:
        model = Test
        fields = ["id", "problem", "stdin", "expected_output"]

    def create(self, validated_data):
        return Test.objects.create(**validated_data)


class ProblemSerializer(serializers.ModelSerializer):
    
    class Meta:
        model = Problem
        fields = ["id", "title", "description", "input_format", "output_format", "time_limit",
                  "memory_limit"]

    def create(self, validated_data):
        validated_data["author"] = self.context["request"].user
        problem = Problem.objects.create(**validated_data)

        return problem
