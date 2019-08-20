from django.db import models
from buildinginfo.models import Building
from django.utils.text import slugify
from django.utils import timezone
from django.conf import settings
import datetime


class Board(models.Model):
    notice = models.BooleanField(default=False, verbose_name=u'공지글 등록')
    BOARD_CHOICES = (
        ('N', '공지사항'), # Notice
        ('FB', '커뮤니티'), # Free-Board
    )
    board_name = models.CharField(max_length=30, choices=BOARD_CHOICES, default='notice')
    building = models.ForeignKey(Building, verbose_name=u'빌딩', on_delete=models.CASCADE)
    author = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
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


class Comment(models.Model):
    board = models.ForeignKey(Board, on_delete=models.CASCADE)
    author = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    text = models.TextField()
    registration = models.DateTimeField(default=timezone.now)

    def __str__(self):
        return str(self.registration)


class SubComment(models.Model):
    comment = models.ForeignKey(Comment, on_delete=models.CASCADE)
    author = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    text = models.TextField()
    registration = models.DateTimeField(default=timezone.now)

