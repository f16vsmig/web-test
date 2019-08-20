from django.conf.urls import url
from django.urls import include, path
from . import views


app_name = 'board'

urlpatterns = [
    path('<str:board_name>/', views.BoardView.as_view(), name='notice_main'),
    path('post/new/', views.post_create, name='post_create'),
    path('post/update/<int:pk>/', views.post_update, name='post_update'),
    path('post/delete/<int:pk>/', views.post_delete, name='post_delete'),
    path('image/delete/<int:pk>/', views.image_delete, name='image_delete'),
    path('comment/new/', views.comment_create, name='comment_create'),
    path('comment/delete/<int:pk>/', views.comment_delete, name='comment_delete'),
    path('subcomment/new', views.subcomment_create, name='subcomment_create'),
    path('subcomment/delete/<int:pk>/', views.subcomment_delete, name='subcomment_delete')
]