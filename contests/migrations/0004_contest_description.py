# Generated by Django 5.1.4 on 2024-12-30 13:06

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('contests', '0003_contestproblem_letter'),
    ]

    operations = [
        migrations.AddField(
            model_name='contest',
            name='description',
            field=models.TextField(blank=True, null=True),
        ),
    ]
