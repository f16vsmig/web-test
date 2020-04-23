import decimal
import datetime
from django import template
from django.db.models import Sum
from django.db import connection
from ..models import Ismart

register = template.Library()


@register.filter(name='sub')
def subtract_filter(value, arg):
    return int(value) - int(arg)


@register.simple_tag(name='sub')
def subtract_tag(value, arg):
    return int(value) - int(arg)


@register.simple_tag(name='add')
def add_tag(value_1, value_2):
    return (value_1 + value_2)


@register.filter(name='count')
def value_count(value, pk):
    return value.filter(pk=pk).count()


@register.filter(name='since')
def cal_days_ago(value):
    date = datetime.datetime.strptime(value, '%Y-%m-%d')
    today = datetime.datetime.today()
    days = (today - date).days
    return f'{days}일전'


@register.simple_tag(name="ratio")
def calculate_ratio(value, total):
    try:
        result = (value / total) * 100
        result = round(result, 2)
        return result
    except:
        return '-'


@register.simple_tag(name="start")
def last_year(years_ago, month, day):
    year = datetime.datetime.today().year + years_ago
    date = datetime.datetime(year, month, day).strftime('%Y-%m-%d')
    return date


@register.filter(name="percentage")
def convert_percentage(value):
    try:
        return value * 100
    except:
        return '-'


@register.filter(name="to_list")
def to_list(queryset_list):
    result = []
    for item in queryset_list:
        result.append(item)
    return result


@register.simple_tag(name="divide")
def divide(value, total):
    if total == '':
        return None
    result = decimal.Decimal(value) / decimal.Decimal(total)
    return result


@register.simple_tag(name="multiply")
def multiply(value, total):
    result = decimal.Decimal(value) * decimal.Decimal(total)
    return round(result, 2)


@register.simple_tag(name="annual_total_kWh")
def ismart_annual_total_kWh(obj, years_ago=None):
    if years_ago is None:
        year = datetime.datetime.today().year
    else:
        year = datetime.datetime.today().year + years_ago
    start = datetime.datetime(year, 1, 1, 1)
    end = datetime.datetime(year + 1, 1, 1, 0)
    queryset = Ismart.objects.filter(
        building=obj, datetime__range=(start, end))
    result = queryset.aggregate(Sum("kWh"))["kWh__sum"]
    if result:
        return round(result, 2)
    else:
        return "-"


@register.simple_tag(name="workingday_total_kWh")
def ismart_annual_workingday_total_kWh(obj, years_ago=None):
    if years_ago is None:
        year = datetime.datetime.today().year
    else:
        year = datetime.datetime.today().year + years_ago
    start = datetime.datetime(year, 1, 1, 1).strftime("%Y-%m-%d %H:00:00")
    end = datetime.datetime(year + 1, 1, 1, 0).strftime("%Y-%m-%d %H:00:00")
    cursor = connection.cursor()

    subquery = f'''
            SELECT DISTINCT \
                buildinginfo_ismart.datetime AS datetime, \
                buildinginfo_ismart."kWh" AS kwh \
            FROM \
                buildinginfo_ismart, scheduler_event \
            WHERE \
                (buildinginfo_ismart.datetime >= scheduler_event.start_time) AND \
                (buildinginfo_ismart.datetime <= scheduler_event.end_time) AND \
                (buildinginfo_ismart.datetime >= '{start}') AND \
                (buildinginfo_ismart.datetime <= '{end}') AND \
                (buildinginfo_ismart.building_id={obj.pk}) \
            ORDER BY \
                datetime ASC
            '''
    query = f'''
            SELECT \
                SUM(t.kwh) \
            FROM \
                ({subquery}) AS t
            '''
    cursor.execute(query)
    result = cursor.fetchall()
    return result[0][0]
