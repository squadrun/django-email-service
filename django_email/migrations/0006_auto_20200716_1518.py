# Generated by Django 3.0.5 on 2020-07-16 09:48

from django.db import migrations


class Migration(migrations.Migration):
    dependencies = [
        ('django_email', '0005_auto_20200716_1446'),
    ]

    operations = [
        migrations.RemoveIndex(
            model_name='emailactivitytracker',
            name='emailactivitytracker_is_active',
        ),
        migrations.RemoveIndex(
            model_name='emaillog',
            name='emaillog_is_active',
        ),
        migrations.RemoveIndex(
            model_name='eventlog',
            name='eventlog_is_active',
        ),
    ]
