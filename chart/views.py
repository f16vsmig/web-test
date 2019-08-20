from django.shortcuts import render

from django.http import HttpResponse  
from django.views.generic import ListView
from buildinginfo.models import Building, Ismart, Weather
from account.models import User
from .utils import field_label_list
import datetime
import json


def ChartView(request):
    username = request.user.get_username()
    user_instance = User.objects.get(email=username)
    if user_instance.is_superuser:
        building_list = Building.objects.all()
    else:
        building_list = Building.objects.filter(author__email=username)

    ismart_fields = field_label_list(Ismart)[3:]
    weather_fields = field_label_list(Weather)[3:]
    context = {
        'building_name': Building.__name__,
        'ismart_name': Ismart.__name__,
        'weather_name': Weather.__name__,
        'building_list': building_list,
        'ismart_fields': ismart_fields,
        'weather_fields': weather_fields,
        'navbar': 'chart',
    }
    return render(request, 'chart/chart.html', context)

def ChartData(request):
    start_day = request.GET.get('start-day')
    end_day = request.GET.get('end-day')
    dt_start_day = datetime.datetime.strptime(start_day, '%Y-%m-%d')
    dt_end_day = datetime.datetime.strptime(end_day, '%Y-%m-%d')+datetime.timedelta(days=1)
    datapoint = request.GET.get('datapoint')
    pk, building, model, endpoint = datapoint.split('-')
    select = {
        "milliseconds": "(EXTRACT(EPOCH FROM datetime)+3600*9)*1000"
    }

    if model == 'Ismart':
        queryset = Ismart.objects.extra(select).filter(building__pk=pk, datetime__range=(dt_start_day, dt_end_day))
    elif model == 'Weather':
        station_id = Building.objects.get(pk=pk).weather_station.station_id
        queryset = Weather.objects.extra(select).filter(weather_station__station_id=station_id, datetime__range=(dt_start_day, dt_end_day))

    data = list(queryset.values_list('milliseconds', endpoint))

    result = {
        'name': datapoint,
        'data': data
    }
    data = json.dumps(result, ensure_ascii=False)
    return HttpResponse(data, content_type="application/json; charset=utf-8")

