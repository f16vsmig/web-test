from django import forms
import datetime

class ChartForm(forms.Form):
    start_day = forms.DateField(widget=forms.DateInput(attrs={"class": "datepicker"}), initial=datetime.date.today())
    end_day = forms.DateField(widget=forms.DateInput(attrs={"class": "datepicker"}), initial=datetime.date.today())
    # end_day = forms.DateTimeField(widget=widgets.SelectDateWidget(years=range(datetime.datetime.now().year-10, datetime.datetime.now().year+1)), initial=datetime.date.today())

    DatetimeOptions = (
        ("hour", "hour"),
        ("day", "day"),
        ("month", "month"),
        ("year", "year"),
        )
    datetime_options = forms.ChoiceField(choices=DatetimeOptions, widget=forms.RadioSelect(), initial="hour")

    ChartType = (
        ("line", "line"),
        ("column", "column"),
        ("area", "area"),
        )
    chart_type = forms.ChoiceField(choices=ChartType, widget=forms.RadioSelect(), initial="line")