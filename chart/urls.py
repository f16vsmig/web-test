from django.conf.urls import url
from django.urls import include, path
from . import views
from django.conf import settings
from django.conf.urls.static import static

app_name = 'chart'

urlpatterns = [
    # path('', views.ChartView.as_view(), name='chart'),
    path('', views.ChartView, name='chart'),
    path('chartdata/', views.ChartData, name='chart_data'),
]
