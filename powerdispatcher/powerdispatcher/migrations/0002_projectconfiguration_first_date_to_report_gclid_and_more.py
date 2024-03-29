# Generated by Django 4.2.2 on 2023-06-09 06:15

from django.db import migrations, models
import django.utils.timezone


class Migration(migrations.Migration):

    dependencies = [
        ('powerdispatcher', '0001_initial'),
    ]

    operations = [
        migrations.AddField(
            model_name='projectconfiguration',
            name='first_date_to_report_gclid',
            field=models.DateField(default=django.utils.timezone.localtime, verbose_name='All tickets from this date will report their gclid'),
        ),
        migrations.AddField(
            model_name='ticket',
            name='empty_callrail_logs',
            field=models.BooleanField(default=False),
        ),
        migrations.AddField(
            model_name='ticket',
            name='has_reported_gclid',
            field=models.BooleanField(default=False),
        ),
        migrations.AddField(
            model_name='ticket',
            name='reported_gclid',
            field=models.BooleanField(default=False),
        ),
        migrations.AddField(
            model_name='ticket',
            name='reported_gclid_at',
            field=models.DateTimeField(blank=True, null=True),
        ),
    ]
