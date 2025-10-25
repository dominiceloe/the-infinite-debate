# Generated manually for security hardening

import django.core.validators
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("debates", "0002_initial"),
    ]

    operations = [
        migrations.AlterField(
            model_name="debate",
            name="topic",
            field=models.TextField(
                help_text="The question or topic being debated",
                validators=[
                    django.core.validators.MinLengthValidator(
                        10, message="Topic must be at least 10 characters long."
                    ),
                    django.core.validators.MaxLengthValidator(
                        1000, message="Topic cannot exceed 1000 characters."
                    ),
                ],
            ),
        ),
    ]
