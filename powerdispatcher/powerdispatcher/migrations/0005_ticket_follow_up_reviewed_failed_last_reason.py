# Generated by Django 5.0.4 on 2024-08-28 18:40

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('powerdispatcher', '0004_ticket_follow_up_reviewed_failed_times'),
    ]

    operations = [
        migrations.AddField(
            model_name='ticket',
            name='follow_up_reviewed_failed_last_reason',
            field=models.IntegerField(default=0),
        ),
    ]
