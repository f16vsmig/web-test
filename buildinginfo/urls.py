from django.conf.urls import url
from django.urls import include, path
from . import views


app_name = 'buildinginfo'

urlpatterns = [
    path('list/', views.BuildingListView.as_view(), name='building_list'),
    path('detail-tilesview/<int:pk>/', views.BuildingDetailView.as_view(), name='building_detail'),
    path('detail-tableview/<int:pk>/', views.BuildingDetailTableView.as_view(), name='building_detail_table'),
    path('notice/<int:pk>/', views.BuildingNoticeView.as_view(), name='building_notice'),
    path('calendar/<int:pk>/', views.BuildingCalender.as_view(), name='building_calendar'),
    path('list/new/', views.BuildingCreateView.as_view(), name='building_new'),
    path('list/update/<int:pk>/', views.BuildingUpdateView.as_view(), name='building_update'),
    path('list/delete/<int:pk>/', views.BuildingDeleteView.as_view(), name='building_delete'),
    path('weather-file-upload/', views.WeatherFileUpload, name='weather_file_upload'),

    path('get-data/<int:pk>/', views.get_energy_data, name='get_data'),
]


