from django.db import migrations


def create_initial_languages(apps, schema_editor):
    Language = apps.get_model('problems', 'Language')

    languages = [
        {"name": "C (GCC 9.2.0)", "language_id": 50},
        {"name": "C# (Mono 6.6.0.161)", "language_id": 51},
        {"name": "C++ (GCC 9.2.0)", "language_id": 54},
        {"name": "Go (1.13.5)", "language_id": 60},
        {"name": "Haskell (GHC 8.8.1)", "language_id": 61},
        {"name": "Java (OpenJDK 13.0.1)", "language_id": 62},
        {"name": "JavaScript (Node.js 12.14.0)", "language_id": 63},
        {"name": "Pascal (FPC 3.0.4)", "language_id": 67},
        {"name": "PHP (7.4.1)", "language_id": 68},
        {"name": "Python (3.11.2)", "language_id": 92},
        {"name": "Rust (1.40.0)", "language_id": 73},
        {"name": "TypeScript (3.7.4)", "language_id": 74},
        {"name": "Kotlin (1.3.70)", "language_id": 78},
        {"name": "SQL (SQLite 3.27.2)", "language_id": 82},
        {"name": "Perl (5.28.1)", "language_id": 85},
    ]

    for lang in languages:
        if not Language.objects.filter(language_id=lang["language_id"]).exists():
            Language.objects.create(name=lang["name"], language_id=lang["language_id"])


class Migration(migrations.Migration):
    dependencies = [
        ('problems', '0002_language_alter_submission_language'),
    ]

    operations = [
        migrations.RunPython(create_initial_languages),
    ]