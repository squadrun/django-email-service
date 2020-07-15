# Generated by Django 3.0.5 on 2020-05-28 07:27

from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("django_email", "0001_initial"),
    ]

    operations = [
        migrations.AlterField(
            model_name="emailactivitytracker",
            name="is_active",
            field=models.BooleanField(
                default=True,
                help_text="Denotes if the object is active or not. Inactive objects behave similar to how a deleted "
                "object works.",
            ),
        ),
        migrations.AlterField(
            model_name="emaillog",
            name="is_active",
            field=models.BooleanField(
                default=True,
                help_text="Denotes if the object is active or not. Inactive objects behave similar to how a deleted "
                "object works.",
            ),
        ),
        migrations.AlterField(
            model_name="eventlog",
            name="is_active",
            field=models.BooleanField(
                default=True,
                help_text="Denotes if the object is active or not. Inactive objects behave similar to how a deleted "
                "object works.",
            ),
        ),
    ]
