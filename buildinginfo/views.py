from django.http import HttpResponse
from django.urls import reverse, reverse_lazy
from django.shortcuts import render, get_object_or_404
from django.views.generic import ListView, DetailView, CreateView, UpdateView, DeleteView
from django.views.generic.edit import FormView, FormMixin
from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import LoginRequiredMixin
from django.utils import timezone
from django.http import Http404, HttpResponseRedirect
from django.contrib import messages
import datetime
import csv
import json
from io import TextIOWrapper

from .models import Building, Ismart, Weather, WeatherStation, Analysis
from .forms import BuildingCreateForm, WeatherFileUploadForm
from .tasks import login_check, ismart_scrap, weather_file_upload, energy_assessment


from account.models import User

from board.views import BoardView
from scheduler.views import BuildingCalendarView

from django.db.models import F, Sum, Count, Case, When, Avg
from django.db import connection


class BuildingListView(ListView):
    model = Building
    template_name = 'buildinginfo/building_list.html'
    extra_context = {
        'navbar': 'buildinginfo',
    }

    def get_queryset(self):
        username = self.request.user.get_username()
        user_instance = User.objects.get(email=username)
        if user_instance.is_superuser:
            queryset = self.model.objects.all()
        else:
            queryset = self.model.objects.filter(author=user_instance)
        return queryset


class BuildingDetailView(DetailView):
    model = Building
    template_name = 'buildinginfo/building_detail.html'
    context_object_name = 'building_obj'
    extra_context = {
        'navbar': 'buildinginfo',
    }

    def get(self, request, *args, **kwargs):
        obj = self.get_object()
        username = request.user.get_username()
        user_instance = User.objects.get(email=username)
        if obj.author == user_instance or user_instance.is_superuser:
            return super().get(request, *args, **kwargs)
        else:
            raise Http404

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['analysis'] = Analysis.objects.filter(building__pk=self.kwargs.get('pk'))
        return context


class BuildingDetailTableView(BuildingDetailView):
    template_name = 'buildinginfo/building_detail_table.html'


class BuildingCreateView(CreateView):
    model = Building
    template_name = 'buildinginfo/building_form.html'
    form_class = BuildingCreateForm
    success_url = reverse_lazy('buildinginfo:building_list')
    extra_context = {
        'navbar': 'buildinginfo',
    }

    def form_valid(self, form):
        ismart_id = self.request.POST.get('ismart_id')
        ismart_pw = self.request.POST.get('ismart_pw')
        start_date = self.request.POST.get('construction_date')
        if login_check(ismart_id, ismart_pw) != True:
            messages.error(self.request, "아이스마트 계정이 유효하지 않습니다.")
        ismart_scrap.delay(ismart_id, ismart_pw, start_date, datetime.datetime.today().strftime('%Y-%m-%d'))
        form.instance.author = self.request.user
        form.instance.registration = timezone.now()
        return super().form_valid(form)


class BuildingUpdateView(UpdateView):
    model = Building
    template_name = 'buildinginfo/building_form.html'
    form_class = BuildingCreateForm
    extra_context = {
        'navbar': 'buildinginfo',
    }

    def get(self, request, *args, **kwargs):
        obj = self.get_object()
        username = request.user.get_username()
        user_instance = User.objects.get(email=username)
        if obj.author == user_instance or user_instance.is_superuser:
            return super().get(request, *args, **kwargs)
        else:
            raise Http404


class BuildingDeleteView(DeleteView):
    model = Building
    success_url = reverse_lazy('buildinginfo:building_list')

    def delete(self, request, *args, **kwargs):
        obj = self.get_object()
        success_url = self.get_success_url()
        username = request.user.get_username()
        user_instance = User.objects.get(email=username)
        if obj.author == user_instance or user_instance.is_superuser:
            obj.delete()
        else:
            raise Http404
        return HttpResponseRedirect(success_url)


def WeatherFileUpload(request):
    if request.method == 'POST':
        form = WeatherFileUploadForm(request.POST, request.FILES)
        if form.is_valid():
            f = TextIOWrapper(request.FILES['file'].file, encoding='euc-kr')
            reader = csv.reader(f)
            next(reader, None)
            for row in reader:
                Weather.objects.update_or_create(
                    weather_station=WeatherStation.objects.get(station_id=row[0]),
                    datetime=datetime.datetime.strptime(row[1], "%Y-%m-%d %H:%M"),
                    defaults={
                        'temp': (None if row[2] == '' else float(row[2])),
                        'rain': (None if row[3] == '' else float(row[3])),
                        'wind': (None if row[4] == '' else float(row[4])),
                        'wind_direction': (None if row[5] == '' else int(row[5])),
                        'humidity': (None if row[6] == '' else int(row[6])),
                        'vapor_pressure': (None if row[7] == '' else float(row[7])),
                        'dewpoint': (None if row[8] == '' else float(row[8])),
                        'field_elecation_pressure': (None if row[9] == '' else float(row[9])),
                        'sealevel_pressure': (None if row[10] == '' else float(row[10])),
                        'daylight_hours': (None if row[11] == '' else float(row[11])),
                        'irradiation_amount': (None if row[12] == '' else float(row[12])),
                        'snowfall_amount': (None if row[13] == '' else float(row[13])),
                        'snowfall_3h': (None if row[14] == '' else float(row[14])),
                        'cloud_total': (None if row[15] == '' else int(row[15])),
                        'cloud_lower': (None if row[16] == '' else int(row[16])),
                        'cloud_shape': str(row[17]),
                        'cloud_ft': (None if row[18] == '' else int(row[18])),
                        'visibility': (None if row[19] == '' else int(row[19])),
                        'WMO_code': (None if row[20] == '' else int(row[20])),
                        'phenomenon_no': (None if row[21] == '' else int(row[21])),
                        'temp_surfice': (None if row[22] == '' else float(row[22])),
                        'temp_under_5cm': (None if row[23] == '' else float(row[23])),
                        'temp_under_10cm': (None if row[24] == '' else float(row[24])),
                        'temp_under_20cm': (None if row[25] == '' else float(row[25])),
                        'temp_under_30cm': (None if row[26] == '' else float(row[26])),
                    }
                )
                # print('{}번행 저장 완료'.format(row[1]), end='\r')
        
        return reverse('buildinginfo:weather_file_upload')
    else:
        form = WeatherFileUploadForm()
    return render(request, 'buildinginfo/weather_file_upload.html', {
        'form': form,
        'navbar': 'buildinginfo',
        })


def get_energy_data(request, pk):

    result = energy_assessment(pk)
    data = json.dumps(result, ensure_ascii=False)
    return HttpResponse(data, content_type="application/json; charset=utf-8")


class BuildingNoticeView(BoardView):
    template_name = 'buildinginfo/building_notice.html'
    board_name = 'notice'
    extra_context = {
        'navbar': 'buildinginfo',
    }

    def get_queryset(self):
        building_pk = self.kwargs.get('pk')
        queryset = self.model.objects.filter(board_name=self.get_board_name(self.board_name), notice='False', building__pk=building_pk).order_by('-pk')
        return queryset

    def get_context_data(self, **kwargs):
        context = super(BuildingNoticeView, self).get_context_data(**kwargs)
        context['building_obj'] = Building.objects.get(pk=self.kwargs.get('pk'))
        context['notice'] = self.model.objects.filter(board_name=self.get_board_name(self.board_name), notice='True').order_by('-registration')
        context['building_list'] = Building.objects.all()
        return context


class BuildingCalender(BuildingCalendarView):
    template_name = 'buildinginfo/building_calendar.html'
    extra_context = {
        'navbar': 'buildinginfo',
    }