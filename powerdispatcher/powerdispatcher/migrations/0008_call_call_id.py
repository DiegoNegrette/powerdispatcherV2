# Generated by Django 5.0.4 on 2024-11-27 01:50

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('powerdispatcher', '0007_call'),
    ]

    operations = [
        migrations.AddField(
            model_name='call',
            name='call_id',
            field=models.CharField(blank=True, max_length=255, null=True),
        ),
    ]