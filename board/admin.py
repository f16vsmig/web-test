from django.contrib import admin
from .models import Board, Images, Comment, SubComment

@admin.register(Board)
class NoticeAdmin(admin.ModelAdmin):
    list_display = ['board_name', 'building', 'author', 'title', 'memo', 'hits', 'registration']
    list_display_links = ['title']
    list_filter = ['board_name', 'building', 'author']

@admin.register(Images)
class ImagesAdmin(admin.ModelAdmin):
    list_display = ['board', 'image']
    list_display_links = ['board']

# @admin.register(Comment)
# class ImagesAdmin(admin.ModelAdmin):
#     list_display = ['board', 'author']
#     list_display_links = ['board']

# @admin.register(SubComment)
# class ImagesAdmin(admin.ModelAdmin):
#     list_display = ['comment', 'author']
#     list_display_links = ['comment']
