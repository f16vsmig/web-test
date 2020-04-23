from django.forms import modelformset_factory
from board.forms import PostForm, ImageForm
from board.models import Images
from django.http import HttpResponse
from django.urls import reverse, reverse_lazy
from django.shortcuts import render, get_object_or_404
from django.views.generic import ListView, DetailView, CreateView, UpdateView, DeleteView
from django.views.generic.edit import FormView, FormMixin
from django.contrib.auth.decorators import login_required, permission_required
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib import messages
from django.utils import timezone
from django.http import Http404, HttpResponseRedirect
import datetime
import csv
import json
from io import TextIOWrapper

from .models import Building, Ismart, Weather, WeatherStation, Analysis
from .forms import BuildingCreateForm, BuildingUpdateForm, WeatherFileUploadForm, WeatherStationCreateForm
from .tasks import login_check, weather_file_upload, IsmartCrawlerTask, EnergyAssessment, EnergyStatistics


from account.models import User

from board.views import BoardView
from scheduler.views import BuildingCalendarView

from django.db.models import F, Sum, Count, Case, When, Avg
from django.db import connection


def weather_station_create(request):
    if request.method == 'POST':
        form = WeatherStationCreateForm(request.POST)
        if form.is_valid():
            form.save()
        return HttpResponse(status=204)
    else:
        form = WeatherStationCreateForm()
        template_name = 'buildinginfo/weather_station_form.html'
        context = {}
        context['form'] = form
        return render(request, template_name, context)


def custom_queryset(info):
    '''
    로그인 된 유저가 작성한 빌딩정보만 요청할 수 있음
    단, 수퍼유저는 모든 빌딩정보를 요청함
    '''
    author = User.objects.get(nickname=info.request.user)
    if author.is_superuser:
        queryset = info.model.objects.all()
    else:
        queryset = info.model.objects.filter(author=author)
    return queryset


class BuildingListView(ListView):
    model = Building
    template_name = 'buildinginfo/building_list.html'
    extra_context = {
        'navbar': 'buildinginfo',
    }

    def get_queryset(self):
        # username = self.request.user.get_username()
        # user_instance = User.objects.get(email=username)
        # if user_instance.is_superuser:
        #     queryset = self.model.objects.all()
        # else:
        #     queryset = self.model.objects.filter(author=user_instance)
        # return queryset

        return custom_queryset(self)


class BuildingDetailView(DetailView):
    model = Building
    template_name = 'buildinginfo/building_detail.html'
    context_object_name = 'building_object'
    extra_context = {
        'navbar': 'buildinginfo',
    }

    # 로그인 된 유저가 작성한 빌딩 정보만 접근할 수 있음. 수퍼유저인 경우 모든 빌딩에 접근 가능.
    def get_queryset(self):
        # return custom_queryset(self)
        author = User.objects.get(nickname=self.request.user)
        if author.is_superuser:
            queryset = self.model.objects.all()
        else:
            queryset = self.model.objects.filter(author=author)
        return queryset

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        building = Building.objects.get(pk=self.kwargs['pk'])
        statistics = EnergyStatistics().get_annual_statistics(building)
        context['stat'] = statistics
        context['building_list'] = Building.objects.values_list(
            'id', flat=True)
        return context


def get_annual_statistics(request, pk):
    building = Building.objects.get(pk=pk)
    data = EnergyStatistics().get_annual_statistics(building)
    json_data = json.dumps(data, ensure_ascii=False)
    return HttpResponse(json_data, content_type="application/json")


def get_annual_statistics_all(request):
    data = EnergyStatistics().get_annual_statistics_all()
    json_data = json.dumps(data, ensure_ascii=False)
    return HttpResponse(json_data, content_type="application/json")


def get_daily_data(request, pk):
    building = Building.objects.get(pk=pk)
    x_axis = request.GET['xaxis']
    y_axis = request.GET['yaxis']
    start = request.GET.get('start')
    end = request.GET.get('end')
    data = EnergyStatistics(start, end).get_daily_data(
        building, x_axis, y_axis)
    json_data = json.dumps(data, ensure_ascii=False)
    return HttpResponse(json_data, content_type="application/json")


def get_monthly_data(request, pk):
    building = Building.objects.get(pk=pk)
    x_axis = request.GET['xaxis']
    y_axis = list(request.GET['yaxis'].split(','))
    data = EnergyStatistics().get_monthly_data(building, x_axis, y_axis)
    json_data = json.dumps(data, ensure_ascii=False)  # 한글 출력시 false 설정
    return HttpResponse(json_data, content_type="application/json")


def get_annual_data(request):
    x_axis = request.GET['xaxis']
    y_axis = request.GET['yaxis'].split(',')
    annotation = request.GET.get('annotation')
    data = EnergyStatistics().get_annual_data(x_axis, y_axis, annotation)
    json_data = json.dumps(data, ensure_ascii=False)  # 한글 출력시 false 설정
    return HttpResponse(json_data, content_type="application/json")


def get_annual_data_group_by(request):
    x_axis = request.GET['xaxis']
    y_axis = request.GET['yaxis'].split(',')
    data = EnergyStatistics().get_annual_data_group_by(x_axis, y_axis)
    json_data = json.dumps(data, ensure_ascii=False)  # 한글 출력시 false 설정
    return HttpResponse(json_data, content_type="application/json")


def get_annual_data_for_one(request, pk):
    building = Building.objects.get(pk=pk)
    x_axis = request.GET['xaxis']
    y_axis = list(request.GET['yaxis'].split(','))
    data = EnergyStatistics().get_annual_data_for_one(building, x_axis, y_axis)
    json_data = json.dumps(data, ensure_ascii=False)  # 한글 출력시 false 설정
    return HttpResponse(json_data, content_type="application/json")


def get_pie_data(request, pk):
    building = Building.objects.get(pk=pk)
    y_axis = list(request.GET['yaxis'].split(','))
    data = EnergyStatistics().get_pie_data(building, y_axis)
    json_data = json.dumps(data, ensure_ascii=False)  # 한글 출력시 false 설정
    return HttpResponse(json_data, content_type="application/json")


class BuildingDetailTableView(BuildingDetailView):
    template_name = 'buildinginfo/building_detail_table.html'


class BuildingCreateView(CreateView):
    # model = Building
    template_name = 'buildinginfo/building_form.html'
    form_class = BuildingCreateForm
    success_url = reverse_lazy('buildinginfo:building_list')
    extra_context = {
        'navbar': 'buildinginfo',
    }

    def form_valid(self, form):
        ismart_id = self.request.POST.get('ismart_id')
        ismart_pw = self.request.POST.get('ismart_pw')
        if (not login_check(ismart_id, ismart_pw)):
            messages.add_message(self.request, messages.ERROR,
                                 '아이스마트 정보가 유효하지 않습니다.')
            return render(self.request, template_name=self.template_name, context=self.get_context_data())

        form.instance.registration = timezone.now()
        self.object = form.save()

        user = User.objects.get(nickname=self.request.user)
        self.object.author.add(user)

        self.ismart_crawling()
        # EnergyAssessment.delay(self.kwargs['pk'])

        # ismart_id = self.request.POST.get('ismart_id')
        # ismart_pw = self.request.POST.get('ismart_pw')
        # start_date = self.request.POST.get('construction_date')
        # IsmartCrawlerTask.delay(
        #     ismart_id, ismart_pw, start_date, datetime.datetime.today().strftime('%Y-%m-%d'))
        return HttpResponseRedirect(self.get_success_url())

    def ismart_crawling(self):
        ismart_id = self.request.POST.get('ismart_id')
        ismart_pw = self.request.POST.get('ismart_pw')
        start_date = self.request.POST.get('construction_date')
        IsmartCrawlerTask.delay(
            ismart_id, ismart_pw, start_date, datetime.datetime.today().strftime('%Y-%m-%d'))


def assessment_view(request, pk):
    EnergyAssessment.delay(pk)
    return HttpResponse(status=204)


class BuildingUpdateView(UpdateView):
    model = Building
    template_name = 'buildinginfo/building_form.html'
    form_class = BuildingUpdateForm
    extra_context = {
        'navbar': 'buildinginfo',
    }

    def form_valid(self, form):
        """
        유저가 작성자와 같거나 슈퍼유저일 때 저장한다.
        만약 ismart 패스워드를 입력하지 않으면 기존 패스워드를 저장한다.
        """
        user = User.objects.get(nickname=self.request.user)
        if self.object.author == user or user.is_superuser:
            if form.instance.ismart_pw == '':
                building_object = Building.objects.get(pk=self.kwargs['pk'])
                form.instance.ismart_pw = building_object.ismart_pw
            self.object = form.save()
            return HttpResponseRedirect(self.get_success_url())
        else:
            raise Http404

    def get_success_url(self):
        return reverse_lazy('buildinginfo:building_detail', kwargs={
            'pk': self.object.pk})


class BuildingDeleteView(DeleteView):
    model = Building
    success_url = reverse_lazy('buildinginfo:building_list')

    def delete(self, request, *args, **kwargs):
        ''' 유저가 작성자와 같거나 슈퍼유저일 때 삭제한다. '''
        self.object = self.get_object()
        success_url = self.get_success_url()
        user = User.objects.get(nickname=request.user)
        if self.object.author == user or user.is_superuser:
            self.object.delete()
            return HttpResponseRedirect(success_url)
        else:
            raise Http404


def WeatherFileUpload(request):
    if request.method == 'POST':
        form = WeatherFileUploadForm(request.POST, request.FILES)
        if form.is_valid():
            f = TextIOWrapper(request.FILES['file'].file, encoding='euc-kr')
            reader = csv.reader(f)
            next(reader, None)
            for row in reader:
                Weather.objects.update_or_create(
                    weather_station=WeatherStation.objects.get(
                        station_id=row[0]),
                    datetime=datetime.datetime.strptime(
                        row[2], "%Y-%m-%d %H:%M"),
                    defaults={
                        'temp': (None if row[3] == '' else float(row[3])),
                        'rain': (None if row[5] == '' else float(row[5])),
                        'wind': (None if row[7] == '' else float(row[7])),
                        'wind_direction': (None if row[9] == '' else int(row[9])),
                        'humidity': (None if row[11] == '' else float(row[11])),
                        'vapor_pressure': (None if row[13] == '' else float(row[13])),
                        'dewpoint': (None if row[14] == '' else float(row[14])),
                        'field_elecation_pressure': (None if row[15] == '' else float(row[15])),
                        'sealevel_pressure': (None if row[17] == '' else float(row[17])),
                        'daylight_hours': (None if row[19] == '' else float(row[19])),
                        'irradiation_amount': (None if row[21] == '' else float(row[21])),
                        'snowfall_amount': (None if row[22] == '' else float(row[22])),
                        'snowfall_3h': (None if row[23] == '' else float(row[23])),
                        'cloud_total': (None if row[24] == '' else int(row[24])),
                        'cloud_lower': (None if row[25] == '' else int(row[25])),
                        'cloud_shape': str(row[26]),
                        'cloud_ft': (None if row[27] == '' else int(row[27])),
                        'visibility': (None if row[28] == '' else int(row[28])),
                        'WMO_code': (None if row[29] == '' else int(row[29])),
                        'phenomenon_no': (None if row[30] == '' else int(row[30])),
                        'temp_surfice': (None if row[31] == '' else float(row[31])),
                        'temp_under_5cm': (None if row[33] == '' else float(row[33])),
                        'temp_under_10cm': (None if row[34] == '' else float(row[34])),
                        'temp_under_20cm': (None if row[35] == '' else float(row[35])),
                        'temp_under_30cm': (None if row[36] == '' else float(row[36])),
                    }
                )
                # print('{}번행 저장 완료'.format(row[1]), end='\r')

        return HttpResponseRedirect(reverse('buildinginfo:weather_file_upload'))
    else:
        form = WeatherFileUploadForm()
    return render(request, 'buildinginfo/weather_file_upload.html', {
        'form': form,
        'navbar': 'buildinginfo',
    })


# def get_energy_data(request, pk):

#     result = energy_assessment(pk)
#     data = json.dumps(result, ensure_ascii=False)
#     return HttpResponse(data, content_type="application/json; charset=utf-8")


class BuildingNoticeView(BoardView):
    template_name = 'buildinginfo/building_notice.html'
    board_name = 'notice'
    extra_context = {
        'navbar': 'buildinginfo',
    }

    def get_queryset(self):
        building_pk = self.kwargs.get('pk')
        queryset = self.model.objects.filter(board_name=self.get_board_name(
            self.board_name), notice='False', building__pk=building_pk).order_by('-pk')
        return queryset

    def get_context_data(self, **kwargs):
        context = super(BuildingNoticeView, self).get_context_data(**kwargs)
        building = Building.objects.get(pk=self.kwargs['pk'])
        context['building_object'] = building
        context['notice'] = self.model.objects.filter(board_name=self.get_board_name(
            self.board_name), notice='True').order_by('-registration')
        context['building_list'] = Building.objects.all()
        context['analysis'] = Analysis.objects.filter(
            building=building).first()
        context['board_name'] = self.board_name
        return context


def notice_create_view(request, pk):
    building = Building.objects.get(pk=pk)
    template_name = 'buildinginfo/notice_form.html'
    board_name = 'notice'
    postForm = PostForm()
    postForm.fields["building"].initial = building
    ImageFormSet = modelformset_factory(Images, form=ImageForm, extra=3)
    # 'extra' means the number of photos that you can upload   ^
    formset = ImageFormSet(queryset=Images.objects.none())

    context = {}
    context['post_form'] = postForm
    context['formset'] = formset
    context['action'] = reverse('board:post_create') + "?board=" + board_name
    context['building_object'] = building
    return render(request, template_name, context)


class BuildingCalender(DetailView):
    """
    빌딩별 캘린더 기능 구현
    """
    model = Building
    template_name = 'buildinginfo/building_calendar.html'
    context_object_name = 'building_object'
    extra_context = {
        'navbar': 'buildinginfo'
    }

    def get_context_data(self, *args, **kwargs):
        context = super().get_context_data(*args, **kwargs)
        building = Building.objects.get(pk=self.kwargs['pk'])
        context['analysis'] = Analysis.objects.filter(
            building=building).first()  # get or none
        context['ismart'] = Ismart.objects.filter(building=building)
        return context
