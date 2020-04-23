from django import forms
from .models import Event


class EventCreateForm(forms.ModelForm):

    class Meta:
        model = Event
        fields = '__all__'
        widgets = {
            'start_time': forms.DateTimeInput(
                attrs={
                    'class': 'datetimepicker',
                }
            ),
            'end_time': forms.DateTimeInput(
                attrs={
                    'class': 'datetimepicker',
                }
            ),
        }
