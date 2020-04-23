import datetime
import os

from django.db import models
from django.utils.text import slugify
from django.utils import timezone
from django.conf import settings
from django.dispatch import receiver

from buildinginfo.models import Building, Facility, EquipmentList


class TaskList(models.Model):
    equip = models.ForeignKey(EquipmentList, on_delete=models.CASCADE)
    name = models.CharField(max_length=50)
    memo = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        sign = '{0}-{1}'
        return sign.format(self.equip, self.name)


class Task(models.Model):
    author = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    facility = models.ForeignKey(Facility, on_delete=models.CASCADE)
    task = models.ForeignKey(
        TaskList, on_delete=models.CASCADE)
    title = models.CharField(max_length=50)
    STATUS_CHOICES = (
        ('ISS', '의뢰'),  # Issue
        ('DRO', '드랍'),  # Drop
        ('PRO', '진행'),  # Progression
        ('COM', '완료')   # Complete
    )
    status = models.CharField(
        max_length=10, choices=STATUS_CHOICES, default='ISS')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        sign = '{0}-{1}'
        return sign.format(self.facility.building, self.title)


class Massage(models.Model):
    task = models.ForeignKey(Task, on_delete=models.CASCADE)
    author = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True)
    memo = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        sign = '{0}-{1}'
        return sign.format(self.task, self.created_at)


def get_image_file_path(instance, filename):
    name = instance.task.building
    slug = slugify(name)
    today = datetime.datetime.today()
    return f"images/tasks/{slug}/{today.year}/{today.month}/{today.day}/{filename}"


class Images(models.Model):
    massage = models.ForeignKey(
        Massage, on_delete=models.CASCADE)
    image = models.ImageField(
        upload_to=get_image_file_path, null=True, default=None)


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
