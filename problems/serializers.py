from rest_framework import serializers

from problems.models import Problem, Test, ProblemTag


class ProblemTagSerializer(serializers.ModelSerializer):
    class Meta:
        model = ProblemTag
        fields = ["id", "name"]


class TestSerializer(serializers.ModelSerializer):
    problem = serializers.PrimaryKeyRelatedField(queryset=Problem.objects.all())

    class Meta:
        model = Test
        fields = ["id", "problem", "stdin", "expected_output"]

    def create(self, validated_data):
        return Test.objects.create(**validated_data)


class ProblemSerializer(serializers.ModelSerializer):
    # tags = ProblemTagSerializer(many=True)
    # tests = TestSerializer(many=True)

    class Meta:
        model = Problem
        fields = ["id", "title", "description", "input_format", "output_format", "time_limit",
                  "memory_limit"]  # TODO: implement tests and tags

    def create(self, validated_data):
        # tags_data = validated_data.pop("tags")
        validated_data["author"] = self.context["request"].user
        problem = Problem.objects.create(**validated_data)

        # for tag_data in tags_data:
        #     tag, created = ProblemTag.objects.get_or_create(name=tag_data["name"])
        #     problem.tags.add(tag)

        return problem
