from django import forms
from account.models import User

from django.utils.translation import ugettext_lazy as _
from django.utils import timezone
from django.http import HttpResponse

from .models import Task, TaskList


class TaskCreateForm(forms.ModelForm):

    class Meta:
        model = Task
        fields = ('facility', 'task', 'title')
