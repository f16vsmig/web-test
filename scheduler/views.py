from django.shortcuts import render, get_object_or_404
from django.views.generic import ListView, DetailView, CreateView, UpdateView, DeleteView
from django.shortcuts import redirect
from django.http import HttpResponse, HttpResponseRedirect, Http404
from django.urls import reverse_lazy, resolve

from .models import Event
from account.models import User
from buildinginfo.models import Building, Ismart, Weather
from .forms import EventForm

# 스케줄러 구현
import datetime
import calendar
from django.utils.safestring import mark_safe
from .utils import Calendar, BuildingCalendar


class CalendarView(ListView):
    model = Event
    form_class = EventForm
    template_name = 'scheduler/calendar.html'
    extra_context = {
        'navbar': 'buildinginfo'
    }

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        date = self.get_date(self.request.GET.get('month', None))
        cal = Calendar(date.year, date.month)
        cal.setfirstweekday(6)  # 주의 시작을 일요일로 설정
        html_cal = cal.formatmonth(self.request, withyear=True)
        events = cal.events.order_by('-start_time')
        username = self.request.user.get_username()
        user_instance = User.objects.get(email=username)
        if user_instance.is_superuser:
            building_objects = Building.objects.all()
        else:
            building_objects = Building.objects.filter(author__email=user_instance)

        context['calendar'] = mark_safe(html_cal)
        context['events'] = events 
        context['date'] = date
        context['prev_month'] = self.prev_month(date)
        context['next_month'] = self.next_month(date)
        context['building_objects'] = building_objects
        return context

    def get_date(self, req_day):
        if req_day:
            year, month = (int(x) for x in req_day.split('-'))
            return datetime.date(year, month, day=1)
        return datetime.datetime.today()

    def prev_month(self, date):
        first = date.replace(day=1)
        prev_month = first - datetime.timedelta(days=1)
        month = 'month=' + str(prev_month.year) + '-' + str(prev_month.month)
        return month

    def next_month(self, date):
        days_in_month = calendar.monthrange(date.year, date.month)[1]
        last = date.replace(day=days_in_month)
        next_month = last + datetime.timedelta(days=1)
        month = 'month=' + str(next_month.year) + '-' + str(next_month.month)
        return month



class BuildingCalendarView(ListView):
    model = Event
    form_class = EventForm
    template_name = 'buildinginfo/building_schedule.html'
    extra_context = {
        'navbar': 'buildinginfo'
    }

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        date = self.get_date(self.request.GET.get('month', None))
        cal = BuildingCalendar(date.year, date.month, self.kwargs.get('pk'))
        cal.setfirstweekday(6)  # 주의 시작을 일요일로 설정
        html_cal = cal.formatmonth(self.request, withyear=True)
        events = cal.events.order_by('-start_time')
        username = self.request.user.get_username()
        user_instance = User.objects.get(email=username)
        building_obj = Building.objects.get(pk=self.kwargs.get('pk'))

        context['calendar'] = mark_safe(html_cal)
        context['events'] = events 
        context['date'] = date
        context['prev_month'] = self.prev_month(date)
        context['next_month'] = self.next_month(date)
        context['building_obj'] = building_obj
        return context

    def get_date(self, req_day):
        if req_day:
            year, month = (int(x) for x in req_day.split('-'))
            return datetime.date(year, month, day=1)
        return datetime.datetime.today()

    def prev_month(self, date):
        first = date.replace(day=1)
        prev_month = first - datetime.timedelta(days=1)
        month = 'month=' + str(prev_month.year) + '-' + str(prev_month.month)
        return month

    def next_month(self, date):
        days_in_month = calendar.monthrange(date.year, date.month)[1]
        last = date.replace(day=days_in_month)
        next_month = last + datetime.timedelta(days=1)
        month = 'month=' + str(next_month.year) + '-' + str(next_month.month)
        return month


class EventCreateView(CreateView):
    model = Event
    form_class = EventForm
    template_name = 'scheduler/event.html'

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        if kwargs['instance'] is None:
            kwargs['instance'] = Event()
        if self.request.GET.get('date'):
            date = datetime.datetime.strptime(self.request.GET.get('date'), '%Y-%m-%d')
            kwargs['instance'].start_time = date
            kwargs['instance'].end_time = date + datetime.timedelta(days=1)
        if self.request.GET.get('id'):
            building_pk = self.request.GET.get('id')
            kwargs['instance'].building = Building.objects.get(pk=building_pk)
        return kwargs

    def get_success_url(self):
        return self.request.META['HTTP_REFERER']


class EventUpdateView(UpdateView):
    model = Event
    form_class = EventForm
    template_name = 'scheduler/event.html'

    def get(self, request, *args, **kwargs):
        self.object = self.get_object()
        username = request.user.get_username()
        user_instance = User.objects.get(email=username)
        if self.object in self.model.objects.filter(building__author__email=username) or user_instance.is_superuser:
            context = self.get_context_data(object=self.object)
        else:
            raise Http404
        return self.render_to_response(context)

    def get_success_url(self):
        return self.request.META['HTTP_REFERER']


def EventDeleteView(request, pk):
    model = Event
    instance = get_object_or_404(Event, pk=pk)
    username = request.user.get_username()
    user_instance = User.objects.get(email=username)
    success_url = resolve(request.path_info).url_name
    if instance in model.objects.filter(building__author__email=username) or user_instance.is_superuser:
        instance.delete()
    else:
        Http404
    return HttpResponseRedirect(request.META.get('HTTP_REFERER', '/'))


