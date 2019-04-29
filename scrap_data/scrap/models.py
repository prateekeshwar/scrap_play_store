# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models

# Create your models here.
class Details(models.Model):
    app_id = models.CharField(max_length=255, unique=True)
    app_name = models.CharField(max_length=255)
    app_detail = models.TextField()