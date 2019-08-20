from django import forms
from .models import Event


class EventForm(forms.ModelForm):

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

  def __init__(self, *args, **kwargs):
    # self.user = kwargs.pop('user')
    super().__init__(*args, **kwargs)
    for field in iter(self.fields):
        #get current classes from Meta
        classes = self.fields[field].widget.attrs.get("class")
        if classes is not None:
            classes += " form-control form-control-sm"
        else:
            classes = "form-control form-control-sm"

        self.fields[field].widget.attrs.update({
            'class': classes
        })