# Generated by Django 5.1 on 2024-08-28 13:34

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('powerdispatcher', '0003_ticket_follow_up_given_by_alternative_technician'),
    ]

    operations = [
        migrations.AddField(
            model_name='ticket',
            name='follow_up_reviewed_failed_times',
            field=models.IntegerField(default=0),
        ),
    ]