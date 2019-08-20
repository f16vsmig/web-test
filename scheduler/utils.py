# from datetime import datetime, time, timedelta
import datetime
from calendar import HTMLCalendar
from django.urls import reverse
from .models import Event
from buildinginfo.models import Building, Ismart, Weather
from account.models import User
from django.db.models import F, Sum, Count, Case, When, Max, Min

from django.http import HttpResponse


class Calendar(HTMLCalendar):

    def __init__(self, year=None, month=None):
        self.year = year
        self.month = month
        super(Calendar, self).__init__()

    # formats a day as a td
    # filter events by day
    def formatday(self, date, events, request):
        events_per_day = events.filter(start_time__range=(datetime.datetime.combine(date, datetime.time(0,0,0)), datetime.datetime.combine(date, datetime.time(23,59,0)))).order_by('building', 'start_time')
        event_list = ''
        if events_per_day.count() > 0:
            event_button = 'visible'
            for event in events_per_day:
                if request.GET.get('id'):
                    event_name = event.event
                else:
                    event_name = str(event.building) + '-' + str(event.event)
                event_detail_url = reverse('scheduler:event_detail', args=(event.id,))
                event_delete_url = reverse('scheduler:event_delete', args=(event.id,))
                event_list += f'<li class="text-left"><span class="bg-primary rounded-circle" style="display: inline-block; height: 8px; width: 8px;"></span><span class="event pr-2"><a class="popup" href="{event_detail_url}"><span class="event d-inline-block text-truncate" style="width: 50%;">&nbsp;{event_name}</span><span style="width: 30px;">{event.start_time.strftime("%I:%M %p")}</span></a><a class="event-delete ml-3" href="{event_delete_url}" onclick="return confirm(&#39;이 일정을 삭제하시겠습니까?&#39;)"><i class="event-delete fas fa-times text-danger text-right"></i></a></span></li>'

        else:
            event_button = 'hidden'

        if request.GET.get('id'):
            req_id = request.GET.get('id')
            name = request.GET.get('name')
            building_params = f'&id={req_id}&name={name}'
        else:
            building_params = ''

        if date.month != self.month:
            month_class = ' outside-month'
        else:
            month_class = ''

        if date == datetime.date.today():
            today_class = ' bg-danger rounded-circle text-white'
        else:
            today_class = ''

        return f"<td class='week border border-bottom-0 align-top text-center pt-1{month_class}'><span class='text-center day {date.strftime('%a').lower()}{today_class}' style='display: inline-block; height: 25px; width: 25px;'><a class='popup p-1' href={reverse('scheduler:event_new')}?date={date}{building_params}>{date.day}</a></span><br><span class='bg-danger rounded-circle event-sign' style='visibility: {event_button}; display: inline-block; height: 10px; width: 10px;'></span><ul class='event-list bg-light' style='position: relative; top: -20px;'>{event_list}</ul></td>"


    def sparkline(self, date, ismart):
        start_time = datetime.datetime.combine(date, datetime.time(1,0,0))
        end_time = date + datetime.timedelta(days=1)

        queryset = ismart.extra(
            select={
                'temp': 'buildinginfo_weather.temp'
            },
            tables=[
                'buildinginfo_weather'
            ],
            where=[
                'buildinginfo_ismart.datetime=buildinginfo_weather.datetime',
                # 'buildinginfo_weather.weather_station=3'
            ]
        ).filter(
            datetime__range=(start_time, end_time)
        ).values(
            'datetime', 'temp'
        ).annotate(
            total_kWh=Sum('kWh')
        ).order_by(
            'datetime'
        )
        
        data = queryset.values_list('datetime', 'total_kWh', 'temp')

        if date.month != self.month:
            month_class = ' outside-month'
        else:
            month_class = ''

        sparkline = ''
        if data:
            for item in data:
                time = item[0]
                hour = item[0].hour
                if hour == 0:
                    hour = 24
                elec = "{:,}".format(item[1])
                elec_height = round(item[1]/self.ismart_max*100, 1)
                temp = item[2]
                temp_bottom = round(((temp - self.weather_min) / (self.weather_max + 10 - self.weather_min))*100, 1)
                if temp > 13:
                    color = 'cooling'
                else:
                    color = 'heating'
                sparkline += f'<span class="index" style="width: 4.16666667%;" data-toggle="tooltip" data-placement="top" data-html="true" title="{time}<br>{elec} kWh<br>{temp} &#8451;" data-animation="false"><span class="count electric" style="height: {elec_height}%;"></span><span class="count {color} rounded-circle" style="bottom: {temp_bottom}%; height: 4px; width: 4px; left: calc(50% - 2px);"></span></span>'
        else:
            sparkline += '<span></span>'
        return f"<td class='week border border-top-0{month_class}'><span class='sparkline' style='width: 100%;'> {sparkline} </span></td>"

    # formats a week as a tr
    def formatweek(self, theweek, events, ismart, request, week_num):
        week = ''
        spark = ''
        for day, weekday in theweek:
            if day != 0:
                date = datetime.date(self.year, self.month, day)
            elif day == 0 and week_num == 1: # 첫주 빈 칸에 이전달 날짜 계산해서 넣기
                first_day = datetime.date(self.year, self.month, 1)
                first_weekday = first_day.weekday()
                if weekday == 6:
                    day_delta = (first_weekday) + 1
                else:
                    day_delta = (first_weekday) - weekday
                date = first_day - datetime.timedelta(days=day_delta)
            else: # 마지막주 빈 칸에 다음달 날짜 계산해서 넣기
                last_day = datetime.date(self.year, self.month+1, 1) - datetime.timedelta(days=1)
                last_weekday = last_day.weekday()
                if last_weekday == 6:
                    day_delta = weekday + 1
                else:
                    day_delta = weekday - last_weekday
                date = last_day + datetime.timedelta(days=day_delta)

            week += self.formatday(date, events, request)
            spark += self.sparkline(date, ismart)
        return f'<tr class="weekday"> {week} </tr><tr class="spark ismart-spark"> {spark} </tr>'

    def formatweekheader(self):
        """
        Return a header for a week as a table row.
        """
        s = ''.join(self.formatweekday(i) for i in self.iterweekdays())
        return '<tr class="text-center text-dark">%s</tr>' % s

    # formats a month as a table
    # filter events by year and month
    def formatmonth(self, request, withyear=True):
        username = request.user.get_username()
        user_instance = User.objects.get(email=username)
        
        if user_instance.is_superuser:
            events = Event.objects.filter(start_time__year=self.year, start_time__month=self.month)
            ismart = Ismart.objects.all()
        else:
            events = Event.objects.filter(building__author__email=username, start_time__year=self.year, start_time__month=self.month)
            ismart = Ismart.objects.filter(building__author__email=username)

        weather = Weather.objects.all()

        if request.method == 'GET' and 'id' in request.GET:
            building_pk = request.GET['id']
            events = events.filter(building__pk=building_pk)
            ismart = ismart.filter(building__pk=building_pk)
            station_id = Building.objects.get(pk=building_pk).weather_station.station_id
            weather = weather.filter(weather_station__station_id=station_id)
        else:
            weather = weather.filter(weather_station__station_id=108) # 기상데이터는 서울(108)을 기본값으로 지정
        
        self.events = events # veiws.py에서 접근하기 위해 전역변수 지정
        self.ismart_max = ismart.filter(
            datetime__year=self.year, datetime__month__range=(self.month - 1, self.month + 1)
        ).values(
            'datetime'
        ).annotate(
            total_kWh=Sum('kWh')
        ).aggregate(
            Max('total_kWh')
        )['total_kWh__max']

        self.weather_max = weather.filter(
            datetime__year=self.year, datetime__month__range=(self.month - 1, self.month + 1)
        ).aggregate(
            Max('temp')
        )['temp__max']

        self.weather_min = weather.filter(
            datetime__year=self.year, datetime__month__range=(self.month - 1, self.month + 1)
        ).aggregate(
            Min('temp')
        )['temp__min']

        cal = f'<table border="0" cellpadding="0" cellspacing="0" class="calendar">\n'
        cal += f'{self.formatweekheader()}\n'
        week_num = 1
        for week in self.monthdays2calendar(self.year, self.month):
            cal += f'{self.formatweek(week, events, ismart, request, week_num)}\n'
            week_num += 1
        cal += f'</table>'
        return cal


class BuildingCalendar(HTMLCalendar):

    def __init__(self, year=None, month=None, building_pk=None):
        self.year = year
        self.month = month
        self.building_pk = building_pk
        super(BuildingCalendar, self).__init__()

    # formats a day as a td
    # filter events by day
    def formatday(self, date, events, request):
        events_per_day = events.filter(start_time__range=(datetime.datetime.combine(date, datetime.time(0,0,0)), datetime.datetime.combine(date, datetime.time(23,59,0)))).order_by('building', 'start_time')
        event_list = ''
        if events_per_day.count() > 0:
            event_button = 'visible'
            for event in events_per_day:
                event_name = event.get_event_display()
                event_detail_url = reverse('scheduler:event_detail', args=(event.id,))
                event_delete_url = reverse('scheduler:event_delete', args=(event.id,))
                event_list += f'<li class="event text-left"><span class="bg-primary rounded-circle" style="display: inline-block; height: 8px; width: 8px;"></span><span class="pr-2"><a class="popup" href="{event_detail_url}"><span class="d-inline-block text-truncate">&nbsp;{event_name}</span></a><span class="float-right pr-2"><span class="text-secondary" style="width: 30px;">{event.start_time.strftime("%I:%M %p")}</span><a class="event-delete ml-2" href="{event_delete_url}" onclick="return confirm(&#39;이 일정을 삭제하시겠습니까?&#39;)"><i class="fas fa-times text-danger text-right"></i></a></span></span></li>'

        else:
            event_button = 'hidden'

        if request.GET.get('id'):
            req_id = request.GET.get('id')
            name = request.GET.get('name')
            building_params = f'&id={req_id}&name={name}'
        else:
            building_params = ''

        if date.month != self.month:
            month_class = ' outside-month'
        else:
            month_class = ''

        if date == datetime.date.today():
            today_class = ' bg-danger rounded-circle text-white'
        else:
            today_class = ''

        return f"<td class='week border border-bottom-0 align-top text-center pt-1{month_class}'><span class='text-center day {date.strftime('%a').lower()}{today_class}' style='display: inline-block; height: 25px; width: 25px;'><a class='popup p-1' href={reverse('scheduler:event_new')}?date={date}{building_params}>{date.day}</a></span><br><span class='bg-danger rounded-circle event-sign' style='visibility: {event_button}; display: inline-block; height: 10px; width: 10px;'></span><ul class='event-list bg-light' style='position: relative; top: -20px;'>{event_list}</ul></td>"


    def sparkline(self, date, ismart):
        start_time = datetime.datetime.combine(date, datetime.time(1,0,0))
        end_time = date + datetime.timedelta(days=1)

        queryset = ismart.extra(
            select={
                'temp': 'buildinginfo_weather.temp'
            },
            tables=[
                'buildinginfo_weather'
            ],
            where=[
                'buildinginfo_ismart.datetime=buildinginfo_weather.datetime',
                # 'buildinginfo_weather.weather_station=3'
            ]
        ).filter(
            datetime__range=(start_time, end_time)
        ).values(
            'datetime', 'temp'
        ).annotate(
            total_kWh=Sum('kWh')
        ).order_by(
            'datetime'
        )
        
        data = queryset.values_list('datetime', 'total_kWh', 'temp')

        if date.month != self.month:
            month_class = ' outside-month'
        else:
            month_class = ''

        sparkline = ''
        if data:
            for item in data:
                time = item[0]
                hour = item[0].hour
                if hour == 0:
                    hour = 24
                elec = "{:,}".format(item[1])
                elec_height = round(item[1]/self.ismart_max*100, 1)
                temp = item[2]
                temp_bottom = round(((temp - self.weather_min) / (self.weather_max + 10 - self.weather_min))*100, 1)
                if temp > 13:
                    color = 'cooling'
                else:
                    color = 'heating'
                sparkline += f'<span class="index" style="width: 4.16666667%;" data-toggle="tooltip" data-placement="top" data-html="true" title="{time}<br>{elec} kWh<br>{temp} &#8451;" data-animation="false"><span class="count electric" style="height: {elec_height}%;"></span><span class="count {color} rounded-circle" style="bottom: {temp_bottom}%; height: 4px; width: 4px; left: calc(50% - 2px);"></span></span>'
        else:
            sparkline += '<span></span>'
        return f"<td class='week border border-top-0{month_class}'><span class='sparkline' style='width: 100%;'> {sparkline} </span></td>"

    # formats a week as a tr
    def formatweek(self, theweek, events, ismart, request, week_num):
        week = ''
        spark = ''
        for day, weekday in theweek:
            if day != 0:
                date = datetime.date(self.year, self.month, day)
            elif day == 0 and week_num == 1: # 첫주 빈 칸에 이전달 날짜 계산해서 넣기
                first_day = datetime.date(self.year, self.month, 1)
                first_weekday = first_day.weekday()
                if weekday == 6:
                    day_delta = (first_weekday) + 1
                else:
                    day_delta = (first_weekday) - weekday
                date = first_day - datetime.timedelta(days=day_delta)
            else: # 마지막주 빈 칸에 다음달 날짜 계산해서 넣기
                last_day = datetime.date(self.year, self.month+1, 1) - datetime.timedelta(days=1)
                last_weekday = last_day.weekday()
                if last_weekday == 6:
                    day_delta = weekday + 1
                else:
                    day_delta = weekday - last_weekday
                date = last_day + datetime.timedelta(days=day_delta)

            week += self.formatday(date, events, request)
            spark += self.sparkline(date, ismart)
        return f'<tr class="weekday"> {week} </tr><tr class="spark ismart-spark"> {spark} </tr>'

    def formatweekheader(self):
        """
        Return a header for a week as a table row.
        """
        s = ''.join(self.formatweekday(i) for i in self.iterweekdays())
        return '<tr class="text-center text-dark">%s</tr>' % s

    # formats a month as a table
    # filter events by year and month
    def formatmonth(self, request, withyear=True):
        events = Event.objects.filter(building__pk=self.building_pk, start_time__year=self.year, start_time__month=self.month)
        ismart = Ismart.objects.filter(building__pk=self.building_pk)
        weather_station = Building.objects.get(pk=self.building_pk).weather_station
        weather = Weather.objects.filter(weather_station=weather_station)
        
        self.events = events # veiws.py에서 접근하기 위해 전역변수 지정
        self.ismart_max = ismart.filter(
            datetime__year=self.year, datetime__month__range=(self.month - 1, self.month + 1)
        ).values(
            'datetime'
        ).annotate(
            total_kWh=Sum('kWh')
        ).aggregate(
            Max('total_kWh')
        )['total_kWh__max']

        self.weather_max = weather.filter(
            datetime__year=self.year, datetime__month__range=(self.month - 1, self.month + 1)
        ).aggregate(
            Max('temp')
        )['temp__max']

        self.weather_min = weather.filter(
            datetime__year=self.year, datetime__month__range=(self.month - 1, self.month + 1)
        ).aggregate(
            Min('temp')
        )['temp__min']

        cal = f'<table border="0" cellpadding="0" cellspacing="0" class="calendar">\n'
        cal += f'{self.formatweekheader()}\n'
        week_num = 1
        for week in self.monthdays2calendar(self.year, self.month):
            cal += f'{self.formatweek(week, events, ismart, request, week_num)}\n'
            week_num += 1
        cal += f'</table>'
        return cal