# Generated by Django 5.1.4 on 2024-12-29 16:05

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('contests', '0002_contestsubmission_contest_problem'),
    ]

    operations = [
        migrations.AddField(
            model_name='contestproblem',
            name='letter',
            field=models.CharField(blank=True, max_length=3, null=True),
        ),
    ]