from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from django.contrib.auth.models import Group
from django.utils.translation import ugettext_lazy as _

from .forms import UserCreationForm, UserChangeForm
from .models import User


@admin.register(User)
class UserAdmin(BaseUserAdmin):
    # The forms to add and change user instances
    form = UserChangeForm
    add_form = UserCreationForm

    # 초기 리스트 조회화면 세팅
    list_display = ('get_full_name', 'email', 'nickname', 'role', 'is_active', 'is_staff', 'is_superuser', 'date_joined')
    list_display_links = ('get_full_name',)
    list_filter = ('is_superuser', 'is_active',)
    search_fields = ('email', 'nickname')
    ordering = ('-date_joined',)
    filter_horizontal = ()

    # 세부내용 조회시 화면에 표시할 필드 세팅
    fieldsets = (
        (_('Account'), {'fields': ('email', 'password')}),
        (_('Personal info'), {'fields': ('name', 'company', 'nickname', 'role')}),
        (_('Permissions'), {'fields': ('is_active', 'is_staff', 'is_superuser', 'groups', 'user_permissions')}),
    )
    # 유저 추가시 입력필드 세팅
    add_fieldsets = (
        (None, {
            'classes': ('wide',),
            'fields': ('email', 'nickname', 'password1', 'password2')}
         ),
    )
    

