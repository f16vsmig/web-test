from django.contrib import admin
from django.urls import path, include
from django.views.generic.base import TemplateView
from django.contrib.auth.decorators import login_required
from django.conf.urls.static import static
from django.conf import settings

from decorator_include import decorator_include

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', login_required(TemplateView.as_view(template_name='index.html')), name='home'),
    path('accounts/', include('account.urls', namespace='account')),
    path('buildinginfo/', decorator_include([login_required], ('buildinginfo.urls', 'buildinginfo'))),
    path('scheduler/', decorator_include([login_required], ('scheduler.urls', 'scheduler'))),
    path('chart/', decorator_include([login_required], ('chart.urls', 'chart'))),
    path('board/', decorator_include([login_required], ('board.urls', 'board'))),
    path('permission-denied', login_required(TemplateView.as_view(template_name='permission_denied.html')), name='permission_denied')
]

urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)