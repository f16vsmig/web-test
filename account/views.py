from django.shortcuts import render, redirect
from django.urls import reverse, reverse_lazy
from django.contrib.auth.models import User
from django.contrib.auth import login, logout, authenticate
from django.contrib.auth.decorators import login_required, permission_required
from django.contrib.auth.mixins import LoginRequiredMixin, PermissionRequiredMixin
from django.http import Http404, HttpResponse
from django.conf import settings

# from django.views.generic.edit import CreateView
from django.views.generic import CreateView, ListView, DetailView
from .models import User
from .forms import UserCreationForm


class CreateUserView(CreateView):
    template_name = 'registration/signup.html'
    form_class = UserCreationForm
    success_url = reverse_lazy('home')


class ProfileView(DetailView):
    model = User
    template_name = 'account/profile.html'
    slug_field = 'nickname'
    slug_url_kwarg = 'nickname'

    # def get(self, request, *args, **kwargs):
    #     self.object = self.get_object()
    #     username = request.user.get_username()
    #     if self.object.email != username:
    #         raise Http404
    #     context = self.get_context_data(object=self.object)
    #     return self.render_to_response(context)
