import datetime
import os

from django.db import models
from django.utils.text import slugify
from django.utils import timezone
from django.conf import settings
from django.dispatch import receiver

from buildinginfo.models import Building


class Board(models.Model):
    notice = models.BooleanField(default=False, verbose_name=u'공지글 등록')
    BOARD_CHOICES = (
        ('COMM', '커뮤니티'),  # Community
        ('WORK', '작업의뢰'),  # Free-Board
    )
    board_name = models.CharField(
        max_length=30, choices=BOARD_CHOICES)
    building = models.ForeignKey(
        Building, verbose_name=u'빌딩', on_delete=models.CASCADE)
    author = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    title = models.CharField(max_length=50, verbose_name=u'제목')
    memo = models.TextField(verbose_name=u'본문')
    hits = models.IntegerField(default=0)
    registration = models.DateTimeField(default=timezone.now)

    def __str__(self):
        return self.title


def get_image_filename(instance, filename):
    board_name = instance.board.board_name
    slug = slugify(board_name)
    today = datetime.datetime.today()
    return f"images/board/{slug}/{today.year}/{today.month}/{today.day}/{filename}"


class Images(models.Model):
    board = models.ForeignKey(Board, on_delete=models.CASCADE)
    image = models.ImageField(upload_to=get_image_filename)


### 모델 데이터 삭제시 연결된 파일도 삭제 ###
@receiver(models.signals.post_delete, sender=Images)
def auto_delete_file_on_delete(sender, instance, **kwargs):
    """
    Deletes file from filesystem
    when corresponding `MediaFile` object is deleted.
    """
    if instance.photo:
        if os.path.isfile(instance.photo.path):
            os.remove(instance.photo.path)

### 모델 데이터 변경시 기존 파일 삭제 ###
@receiver(models.signals.pre_save, sender=Images)
def auto_delete_file_on_change(sender, instance, **kwargs):
    """
    Deletes old file from filesystem
    when corresponding `MediaFile` object is updated
    with new file.
    """
    if not instance.pk:
        return False

    try:
        old_file = sender.objects.get(pk=instance.pk).image
    except sender.DoesNotExist:
        return False

    new_file = instance.photo
    if old_file and old_file != new_file:
        if os.path.isfile(old_file.path):
            os.remove(old_file.path)


class Comment(models.Model):
    board = models.ForeignKey(Board, on_delete=models.CASCADE)
    author = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    text = models.TextField(blank=True)
    registration = models.DateTimeField(default=timezone.now)

    def __str__(self):
        return str(self.registration)


class SubComment(models.Model):
    comment = models.ForeignKey(Comment, on_delete=models.CASCADE)
    author = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    text = models.TextField(blank=True)
    registration = models.DateTimeField(default=timezone.now)
