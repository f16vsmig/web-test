from django.conf.urls import url
from django.urls import include, path
from . import views
from django.conf import settings
from django.conf.urls.static import static

app_name = 'scheduler'

urlpatterns = [
    path('calendar/', views.CalendarView.as_view(), name='calendar'),
    path('building-calendar/<int:pk>/', views.BuildingCalendarView.as_view(), name='building_calendar'),
    path('event/new/', views.EventCreateView.as_view(), name='event_new'),
    path('event/detail/<int:pk>/', views.EventUpdateView.as_view(), name='event_detail'),
    path('event/update/<int:pk>/', views.EventUpdateView.as_view(), name='event_update'),
    path('event/delete/<int:pk>/', views.EventDeleteView, name='event_delete'),
]
