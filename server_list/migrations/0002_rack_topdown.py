# Generated by Django 2.1.7 on 2019-02-27 11:42

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('server_list', '0001_initial'),
    ]

    operations = [
        migrations.AddField(
            model_name='rack',
            name='topdown',
            field=models.BooleanField(default=True),
        ),
    ]
