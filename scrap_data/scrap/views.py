# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.shortcuts import render
from django.http import HttpResponse

from scrap import scraper
from django.core.cache import cache

from .models import Details
# Create your views here.


def index(request):
    return render(request, 'scrap/templates/index.html', {})


def return_searched_app_name(request):
    try:
        app_name = request.GET.get('app_name', '')
        if app_name == '':
            return HttpResponse("Send app name in parameter")
        app_detail = scraper.search(app_name)
        return HttpResponse(str(app_detail))
    except Exception as e:
        raise

def return_detail_of_app(request):
    try:
        app_id = request.GET.get('app_id', '')
        cache_result = cache.get(app_id)
        if cache_result is not None:
            return HttpResponse(str(cache_result))
        app_obj = Details.objects.filter(app_id=app_id).first()
        if app_obj is not None:
            app_details = app_obj.app_detail
        else:
            app_details = scraper.details(app_id)
            if app_details is not None:
                Details.objects.create(app_id=app_id,app_name= app_details['title'],app_detail=app_details)
            else:
                return HttpResponse("Please pass valid app id in url Parameter")
        cache.set(app_id, app_details, timeout=None)
        return HttpResponse(str(app_details))
    except Exception as e:
        raise