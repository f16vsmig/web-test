from django import forms
from .models import Building
from account.models import User

from django.utils.translation import ugettext_lazy as _
from django.utils import timezone
from django.http import HttpResponse


class BuildingCreateForm(forms.ModelForm):

    class Meta:
        model = Building
        # fields = '__all__'
        widgets = {
            'construction_date': forms.DateInput(
                attrs={
                    'class': 'date-select datepicker',
                }
            ),
            'ismart_pw': forms.PasswordInput(),
        }
        exclude = ('author', 'registration')

    photo = forms.ImageField(
        widget=forms.FileInput(
            attrs={
                'class': 'form-control-file',
                'placeholder': _('Select Photo'),
                'required': 'False',
            }
        )
    )

    def __init__(self, *args, **kwargs):
        # self.user = kwargs.pop('user')
        super().__init__(*args, **kwargs)
        for field in iter(self.fields):
            #get current classes from Meta
            classes = self.fields[field].widget.attrs.get("class")
            if "form-control-file" == classes:
                pass
            elif classes is not None:
                classes += " form-control"
            else:
                classes = "form-control"
            self.fields[field].widget.attrs.update({
                'class': classes
            })


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