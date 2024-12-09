# Generated by Django 5.0.4 on 2024-08-20 16:55

import django.db.models.deletion
import django.utils.timezone
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('powerdispatcher', '0001_initial'),
    ]

    operations = [
        migrations.AddField(
            model_name='projectconfiguration',
            name='first_date_to_review_follow_up_tickets',
            field=models.DateField(default=django.utils.timezone.localtime, verbose_name='All tickets from this date will be reviewed if they are in follow up state'),
        ),
        migrations.AddField(
            model_name='ticket',
            name='alternative_source',
            field=models.TextField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name='ticket',
            name='alternative_technician',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.PROTECT, related_name='alternative_tickets', to='powerdispatcher.technician'),
        ),
        migrations.AddField(
            model_name='ticket',
            name='follow_up_last_reviewed_at',
            field=models.DateTimeField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name='ticket',
            name='follow_up_reviewed_times',
            field=models.IntegerField(default=0),
        ),
        migrations.AddField(
            model_name='ticket',
            name='follow_up_strategy_successfull',
            field=models.BooleanField(blank=True, null=True),
        ),
    ]
