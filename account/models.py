'''
 계정 커스텀 모델 추가
'''

from django.db import models
from django.contrib.auth.models import BaseUserManager, AbstractBaseUser, PermissionsMixin
from django.utils import timezone
from django.utils.translation import ugettext_lazy as _



class UserManager(BaseUserManager):
    
    def create_user(self, email, nickname, password=None):
        """
        주어진 이메일, 닉네임, 비밀번호 등 개인정보로 User 인스턴스 생성
        """
        if not email:
            raise ValueError(_('Users must have an email address'))

        user = self.model(
            email=self.normalize_email(email),
            nickname=nickname,
        )

        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_staff(self, email, nickname, password):
        """
        주어진 이메일, 닉네임, 비밀번호 등 개인정보로 User 인스턴스 생성
        단, 최상위 사용자이므로 권한을 부여한다. 
        """
        user = self.create_user(
            email=email,
            password=password,
            nickname=nickname,
        )

        user.is_staff = True
        user.save(using=self._db)
        return user

    def create_superuser(self, email, nickname, password):
        user = self.create_user(
            email=email,
            password=password,
            nickname=nickname,
        )
        user.is_staff = True
        user.is_superuser = True
        user.save(using=self._db)
        return user


class User(AbstractBaseUser, PermissionsMixin):
    name = models.CharField(
        verbose_name=_('이름'),
        max_length=30,
        blank=True
    )
    company = models.CharField(
        verbose_name=_('소속'),
        max_length=30,
        blank=True
    )
    email = models.EmailField(
        verbose_name=_('Email address'),
        max_length=255,
        unique=True,
    )
    nickname = models.CharField(
        verbose_name=_('Nickname'),
        max_length=30,
        unique=True
    )
    BuildingOwnner = 'BO'
    CenterOperator = 'CO'
    FieldEngineer = 'FE'
    ROLE_CHOICES = (
        (BuildingOwnner, '건물주'),
        (CenterOperator, '센터운영자'),
        (FieldEngineer, '현장엔지니어')
    )
    role = models.CharField(
        verbose_name=_('Role'),
        choices=ROLE_CHOICES,
        max_length=10,
        blank=True
    )
    is_active = models.BooleanField(
        default=True
    )
    is_staff = models.BooleanField(
        default=False
    )
    date_joined = models.DateTimeField(
        verbose_name=_('Date joined'),
        default=timezone.now
    )

    objects = UserManager()

    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = ['nickname', ]

    class Meta:
        verbose_name = _('user')
        verbose_name_plural = _('users')
        ordering = ('-date_joined',)

    def __str__(self):
        return self.nickname

    def get_full_name(self):        
        return self.nickname

    def get_short_name(self):
        return self.nickname

    get_full_name.short_description = _('Full name')
