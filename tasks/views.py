from django.http import HttpResponse
from django.urls import reverse, reverse_lazy
from django.shortcuts import render, get_object_or_404
from django.views.generic import ListView, DetailView, CreateView, UpdateView, DeleteView
from django.views.generic.edit import FormView, FormMixin
from django.contrib.auth.decorators import login_required, permission_required
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib import messages
from django.utils import timezone
from django.http import Http404, HttpResponseRedirect
import datetime

from buildinginfo.models import Building, Facility
from .models import Task, Massage, Images
from .forms import TaskCreateForm


class TaskListView(ListView):
    model = Task
    context_object_name = 'tasks'
    template_name = 'tasks/tasks.html'
    extra_context = {
        'navbar': 'buildinginfo',
    }

    def get_queryset(self):
        '''
        pk로 필터링 된 태스크만 요청
        '''
        status = self.request.GET.get('status')
        if status:
            queryset = self.model.objects.filter(
                facility__building__pk=self.kwargs.get('pk'), status=status).order_by('-created_at')
        else:
            queryset = self.model.objects.filter(
                facility__building__pk=self.kwargs.get('pk')).order_by('-created_at')
        return queryset

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        tasks = Task.objects.all()
        context['total_tasks_cnt'] = tasks.count()
        context['request_cnt'] = tasks.filter(status='ISS').count()
        context['ing_cnt'] = tasks.filter(status='PRO').count()
        context['complete_cnt'] = tasks.filter(status='COM').count()
        context['drop_cnt'] = tasks.filter(status='DRO').count()
        context['building_object'] = Building.objects.get(pk=self.kwargs['pk'])
        context['massages'] = Massage.objects.filter(
            task__facility__building__pk=self.kwargs.get('pk'))
        context['images'] = Images.objects.filter(
            massage__task__facility__building__pk=self.kwargs.get('pk'))

        return context


# class TaskCreateView(CreateView):
#     form_class = TaskCreateForm
#     template_name = 'tasks/task_form.html'

#     def get_context_data(self, **kwargs):
#         context = super().get_context_data()
#         form = context['form']
#         form.fields['facility'].queryset = Facility.objects.filter(
#             building__pk=self.kwargs.get('pk'))
#         context['form'] = form
#         return context

def task_create_view(request):
    template_name = 'tasks/task_form.html'

    if request.method == 'POST':
        form = TaskCreateForm(request.POST)
        if form.is_valid:
            form.save(commit=False)
            form.instance.author = request.user
            form.save()
            return HttpResponse(status=204)

    else:
        building_pk = request.GET.get('building')
        form = TaskCreateForm()
        form.fields['facility'].queryset = Facility.objects.filter(
            building__pk=building_pk)
        return render(request, template_name, {'form': form})


def task_status_next(request, pk):
    if request.method == 'POST':
        task = Task.objects.get(pk=pk)
        if task.status == 'ISS':
            task.status = 'PRO'
            task.save()
        elif task.status == 'PRO':
            task.status = 'COM'
            task.save()
        return HttpResponseRedirect(request.META.get('HTTP_REFERER'))


def task_drop(request, pk):
    if request.method == 'POST':
        task = Task.objects.get(pk=pk)
        task.status = 'DRO'
        task.save()
        return HttpResponseRedirect(request.META.get('HTTP_REFERER'))
