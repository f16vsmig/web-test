from django.conf.urls import url
from django.urls import include, path
from . import views


app_name = 'tasks'

urlpatterns = [
    path('building/<int:pk>/',
         views.TaskListView.as_view(), name='tasks'),
    #     path('new/<int:pk>/', views.TaskCreateView.as_view(), name='task_create')
    path('new/', views.task_create_view, name='task_create'),
    path('task-next/<int:pk>/', views.task_status_next, name='task_next'),
    path('task-drop/<int:pk>/', views.task_drop, name='task_drop')
]
