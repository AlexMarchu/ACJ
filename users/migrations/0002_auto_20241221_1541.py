from django.db import migrations


def create_initial_roles(apps, schema_editor):
    UserRole = apps.get_model('users', 'UserRole')

    if not UserRole.objects.filter(role='admin').exists():
        UserRole.objects.create(pk=1, role='admin')
    if not UserRole.objects.filter(role='teacher').exists():
        UserRole.objects.create(pk=2, role='teacher')
    if not UserRole.objects.filter(role='student').exists():
        UserRole.objects.create(pk=3, role='student')


class Migration(migrations.Migration):
    dependencies = [
        ('users', '0001_initial'),
    ]

    operations = [
        migrations.RunPython(create_initial_roles),
    ]
