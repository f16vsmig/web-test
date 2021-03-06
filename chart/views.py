from django.db.models.functions import ExtractYear, ExtractMonth, ExtractDay, ExtractHour, ExtractMinute, ExtractSecond
from django.shortcuts import render

from django.http import HttpResponse
from django.views.generic import ListView
from buildinginfo.models import Building, Ismart, Weather
from account.models import User
from .utils import field_label_list
import datetime
import json
from django.db.models.functions import Concat
from django.db.models import F, Value, CharField
import gviz_api


def ChartView(request):
    username = request.user.get_username()
    user_instance = User.objects.get(email=username)
    if user_instance.is_superuser:
        building_object_list = Building.objects.all()
    else:
        building_object_list = Building.objects.filter(author__email=username)
    model_list = [Ismart, Weather]
    # ismart_fields = field_label_list(Ismart)[3:]
    # weather_fields = field_label_list(Weather)[3:]
    # datapoints = ismart_fields + weather_fields
    context = {
        'building_object_list': building_object_list,
        'model_list': model_list,
        # 'ismart_name': Ismart.__name__,
        # 'weather_name': Weather.__name__,
        # 'ismart_fields': ismart_fields,
        # 'weather_fields': weather_fields,
        'navbar': 'chart',
    }
    # return render(request, 'chart/chart.html', context)
    return render(request, 'chart/google_chart.html', context)


def ChartData(request):
    start_day = request.GET.get('start-day')
    end_day = request.GET.get('end-day')
    dt_start_day = datetime.datetime.strptime(start_day, '%Y-%m-%d')
    dt_end_day = datetime.datetime.strptime(
        end_day, '%Y-%m-%d')+datetime.timedelta(days=1)
    datapoint = request.GET.get('datapoint')
    pk, building, model, endpoint = datapoint.split('-')
    select = {
        "milliseconds": "(EXTRACT(EPOCH FROM datetime)+3600*9)*1000"
    }

    if model == 'Ismart':
        queryset = Ismart.objects.extra(select).filter(
            building__pk=pk, datetime__range=(dt_start_day, dt_end_day)).order_by('datetime')
    elif model == 'Weather':
        station_id = Building.objects.get(pk=pk).weather_station.station_id
        queryset = Weather.objects.extra(select).filter(
            weather_station__station_id=station_id, datetime__range=(dt_start_day, dt_end_day)).order_by('datetime')

    data = list(queryset.values_list('milliseconds', endpoint))

    result = {
        'name': datapoint,
        'data': data
    }
    data = json.dumps(result, ensure_ascii=False)
    return HttpResponse(data, content_type="application/json; charset=utf-8")


'''
def GoogleChartData(request):
    start_day = request.GET.get('start-day')
    end_day = request.GET.get('end-day')
    dt_start_day = datetime.datetime.strptime(start_day, '%Y-%m-%d')
    dt_end_day = datetime.datetime.strptime(end_day, '%Y-%m-%d')+datetime.timedelta(days=1)
    datapoint = request.GET.get('datapoint')
    building_pk, building, model, endpoint = datapoint.split('-')

    col_desc = [
        ("date", "datetime"),
        (endpoint, "number")
    ]

    # model에 따라 데이터 조회
    if model == 'Ismart':
        queryset = Ismart.objects.filter(building__pk=building_pk, datetime__range=(dt_start_day, dt_end_day))
    elif model == 'Weather':
        station_id = Building.objects.get(pk=building_pk).weather_station.station_id
        queryset = Weather.objects.filter(weather_station__station_id=station_id, datetime__range=(dt_start_day, dt_end_day))
    data = queryset.values_list('datetime', endpoint)

    data_table = gviz_api.DataTable(col_desc)
    data_table.LoadData(data)

    return HttpResponse(data_table.ToJSon(), content_type="application/json; charset=utf-8")
'''


def GoogleChartData(request):
    start_day = request.GET.get('start-day')
    end_day = request.GET.get('end-day')
    dt_start_day = datetime.datetime.strptime(start_day, '%Y-%m-%d')
    dt_end_day = datetime.datetime.strptime(
        end_day, '%Y-%m-%d')+datetime.timedelta(days=1)
    datapoint = request.GET.get('datapoint')
    building_pk, building, model, endpoint = datapoint.split('-')

    # model에 따라 데이터 조회
    if model == 'Ismart':
        queryset = Ismart.objects.filter(
            building__pk=building_pk, datetime__range=(dt_start_day, dt_end_day)).order_by('datetime')
    elif model == 'Weather':
        station_id = Building.objects.get(
            pk=building_pk).weather_station.station_id
        queryset = Weather.objects.filter(
            weather_station__station_id=station_id, datetime__range=(dt_start_day, dt_end_day)).order_by('datetime')

    queryset = queryset.annotate(
        timestamp=Concat(
            Value('Date('),
            ExtractYear('datetime'), Value(', '),
            ExtractMonth('datetime')-1, Value(', '),
            ExtractDay('datetime'), Value(', '),
            ExtractHour('datetime'), Value(', '),
            ExtractMinute('datetime'), Value(', '),
            ExtractSecond('datetime'), Value(')'),
            output_field=CharField()
        )
    )
    data = queryset.values_list('timestamp', endpoint)
    result = {
        'prop': {'id': datapoint, 'label': building+'-'+model+'-'+endpoint, 'type': 'number'},
        'data': dict((x[0], x[1]) for x in data)
    }

    return HttpResponse(json.dumps(result, ensure_ascii=False), content_type="application/json; charset=utf-8")


'''

from django.core import serializers

from django.core.serializers.python import Serializer

class MySerialiser(Serializer):

    def end_object(self, obj):
        self._current['id'] = obj._get_pk_val()
        self.objects.append(self._current)


def GoogleChartData(request):
    start_day = request.GET.get('start-day')
    end_day = request.GET.get('end-day')
    dt_start_day = datetime.datetime.strptime(start_day, '%Y-%m-%d')
    dt_end_day = datetime.datetime.strptime(end_day, '%Y-%m-%d')+datetime.timedelta(days=1)
    datapoint = request.GET.get('datapoint')
    pk, building, model, endpoint = datapoint.split('-')

    if model == 'Ismart':
        queryset = Ismart.objects.filter(building__pk=pk, datetime__range=(dt_start_day, dt_end_day))
    elif model == 'Weather':
        station_id = Building.objects.get(pk=pk).weather_station.station_id
        queryset = Weather.objects.filter(weather_station__station_id=station_id, datetime__range=(dt_start_day, dt_end_day))
    # data = queryset
    # result = serializers.serialize('json', data)
    # result = serializers.serialize('json', data)
    # result = MySerialiser().serialize(data)

    cols = [
        {'id': 'datetime', 'label': 'datetime', 'type': 'datetime'},
        {'id': endpoint, 'label': endpoint, 'type': 'number'}
    ]

    rows = []
    for obj in queryset:
        row = {}
        row['c'] = []
        row['c'].append({'v': obj.datetime.strftime('Date(%Y, %m, %d, %H, %M, %S)')})
        row['c'].append({'v': getattr(obj, endpoint)})
        rows.append(row)

    result = {
        'cols': cols,
        'rows': rows
    }

    return HttpResponse(json.dumps(result, ensure_ascii=False), content_type="application/json; charset=utf-8")
'''
