# -*- coding: utf-8 -*-
# Generated by Django 1.11.20 on 2019-04-29 08:01
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies = [
    ]

    operations = [
        migrations.CreateModel(
            name='Details',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('app_id', models.CharField(max_length=255, unique=True)),
                ('app_name', models.CharField(max_length=255)),
                ('app_detail', models.TextField()),
            ],
        ),
    ]
