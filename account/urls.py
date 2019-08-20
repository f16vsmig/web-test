from django.conf.urls import url
from django.urls import path, reverse_lazy
from django.contrib.auth.views import LoginView, LogoutView, PasswordChangeView, PasswordChangeDoneView
from django.contrib.auth.decorators import login_required
from . import views, forms

from django.conf import settings
from django.conf.urls.static import static

app_name = 'account'

urlpatterns = [
    path('login/', LoginView.as_view(form_class=forms.LoginForm), name='login'),
    path('logout/', LogoutView.as_view(next_page='/'), name='logout'),
    path('signup/', views.CreateUserView.as_view(), name='signup'),
    path('password_change/', PasswordChangeView.as_view(template_name='registration/password_change.html', success_url=reverse_lazy('account:password_change_done')), name='password_change'),
    path('password_change/done/', PasswordChangeDoneView.as_view(template_name='registration/password_change_success.html'), name='password_change_done'),
    path('profile/<nickname>/', views.ProfileView.as_view(), name='profile'),
]