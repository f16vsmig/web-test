from django import forms
from .models import Building, WeatherStation
from account.models import User

from django.utils.translation import ugettext_lazy as _
from django.utils import timezone
from django.http import HttpResponse


class WeatherStationCreateForm(forms.ModelForm):

    class Meta:
        model = WeatherStation
        fields = '__all__'


class BuildingCreateForm(forms.ModelForm):

    class Meta:
        model = Building
        widgets = {
            'construction_date': forms.DateInput(
                attrs={
                    'class': 'datepicker',
                }
            ),
            'ismart_pw': forms.PasswordInput(),
            'photo': forms.FileInput(
                attrs={
                    'class': 'form-control-file',
                    'placeholder': 'Select Photo',
                }
            )
        }
        exclude = ('author', 'registration')

    # photo = forms.ImageField(
    #     required=False,
    #     widget=forms.FileInput(
    #         attrs={
    #             'class': 'form-control-file',
    #             'placeholder': _('Select Photo'),
    #         }
    #     )
    # )


class BuildingUpdateForm(BuildingCreateForm):

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['ismart_pw'].required = False
        self.fields['ismart_pw'].widget.attrs['placeholder'] = '변경할 경우 입력하세요.'


class WeatherFileUploadForm(forms.Form):

    file = forms.FileField(
        widget=forms.FileInput(
            attrs={
                'class': 'form-control-file',
                'placeholder': _('Select File'),
                'required': 'True',
            }
        )
    )

    # def __init__(self, *args, **kwargs):
    #     # self.user = kwargs.pop('user')
    #     super().__init__(*args, **kwargs)
    #     for field in iter(self.fields):
    #         #get current classes from Meta
    #         classes = self.fields[field].widget.attrs.get("class")
    #         if classes is not None:
    #             classes += " form-control"
    #         else:
    #             classes = "form-control"
    #         self.fields[field].widget.attrs.update({
    #             'class': classes
    #         })
