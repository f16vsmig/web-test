
from django.views.generic.base import TemplateView
from django.urls import include, path
from django.conf.urls import url
from . import views


app_name = 'buildinginfo'

urlpatterns = [
    path('list/', views.BuildingListView.as_view(), name='building_list'),
    path('detail-tilesview/<int:pk>/',
         views.BuildingDetailView.as_view(), name='building_detail'),
    path('detail-tableview/<int:pk>/',
         views.BuildingDetailTableView.as_view(), name='building_detail_table'),


    path('notice/<int:pk>/', views.BuildingNoticeView.as_view(),
         name='building_notice'),
    path('notice/new/<int:pk>', views.notice_create_view,
         name='notice_create'),
    path('calendar/<int:pk>/', views.BuildingCalender.as_view(),
         name='building_calendar'),
    path('list/new/', views.BuildingCreateView.as_view(), name='building_new'),
    path('list/update/<int:pk>/',
         views.BuildingUpdateView.as_view(), name='building_update'),
    path('list/delete/<int:pk>/',
         views.BuildingDeleteView.as_view(), name='building_delete'),
    path('weather-station-create', views.weather_station_create,
         name='weather_station_create'),
    path('weather-file-upload/', views.WeatherFileUpload,
         name='weather_file_upload'),

    #     path('get-data/<int:pk>/', views.get_energy_data, name='get_data'),

    path('assessment/<int:pk>/', views.assessment_view, name="assessment"),

    path('annual-statistics-data/<int:pk>/',
         views.get_annual_statistics, name="annual_statistics"),
    path('annual-statistics-data-all/',
         views.get_annual_statistics_all, name="annual_statistics_all"),
    path('daily-data/<int:pk>/', views.get_daily_data, name="daily_data"),
    path('annual-data-for-one/<int:pk>/',
         views.get_annual_data_for_one, name="annual_data_for_one"),
    path('annual-data/',
         views.get_annual_data, name="annual_data"),
    path('annual-data-group-by/',
         views.get_annual_data_group_by, name="annual_data_group_by"),
    path('monthly-data/<int:pk>/', views.get_monthly_data, name="monthly_data"),
    path('pie-data/<int:pk>/', views.get_pie_data, name="pie_data"),
]
