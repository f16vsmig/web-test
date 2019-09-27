from django.db import models
from django.utils.translation import gettext as _
from django.utils.text import slugify
from django.utils import timezone
from django.conf import settings
from django import template

register = template.Library()


class WeatherStation(models.Model):
    city = models.CharField(max_length=20)
    station_id = models.IntegerField()

    class Meta:
        unique_together = ('city', 'station_id')

    def __str__(self):
        title = str(self.city)+str('_')+str(self.station_id)
        return title


class Weather(models.Model):
    weather_station = models.ForeignKey(WeatherStation, on_delete=models.PROTECT)
    datetime = models.DateTimeField(null=True, blank=True, default=None)
    temp = models.FloatField(null=True, blank=True, default=None)
    rain = models.FloatField(null=True, blank=True, default=None)
    wind = models.FloatField(null=True, blank=True, default=None)
    wind_direction = models.IntegerField(null=True, blank=True, default=None)
    humidity = models.IntegerField(null=True, blank=True, default=None)
    vapor_pressure = models.FloatField(null=True, blank=True, default=None)
    dewpoint = models.FloatField(null=True, blank=True, default=None)
    field_elecation_pressure = models.FloatField(null=True, blank=True, default=None)
    sealevel_pressure = models.FloatField(null=True, blank=True, default=None)
    daylight_hours = models.FloatField(null=True, blank=True, default=None)
    irradiation_amount = models.FloatField(null=True, blank=True, default=None)
    snowfall_amount = models.FloatField(null=True, blank=True, default=None)
    snowfall_3h = models.FloatField(null=True, blank=True, default=None)
    cloud_total = models.IntegerField(null=True, blank=True, default=None)
    cloud_lower = models.IntegerField(null=True, blank=True, default=None)
    cloud_shape = models.CharField(max_length=10, null=True, blank=True, default=None)
    cloud_ft = models.IntegerField(null=True, blank=True, default=None)
    visibility = models.IntegerField(null=True, blank=True, default=None)
    WMO_code = models.IntegerField(null=True, blank=True, default=None)
    phenomenon_no = models.CharField(max_length=50, null=True, blank=True, default=None)
    temp_surfice = models.FloatField(null=True, blank=True, default=None)
    temp_under_5cm = models.FloatField(null=True, blank=True, default=None)
    temp_under_10cm = models.FloatField(null=True, blank=True, default=None)
    temp_under_20cm = models.FloatField(null=True, blank=True, default=None)
    temp_under_30cm = models.FloatField(null=True, blank=True, default=None)

    class Meta:
        unique_together = ('weather_station', 'datetime')

    # def __str__(self):
    #     return str(self.weather_station)

    @register.filter
    def to_class_name(self, value):
        return value.__class__.__name__


def get_image_filename(instance, filename):
    name = instance.name
    slug = slugify(name, allow_unicode=True)
    # today = datetime.datetime.today()
    return f"images/buildinginfo/{instance.pk}-{slug}/{filename}"


class Building(models.Model):
    # author = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.PROTECT)
    author = models.ManyToManyField(settings.AUTH_USER_MODEL)
    weather_station = models.ForeignKey(WeatherStation, on_delete=models.PROTECT)
    name = models.CharField(max_length=20, blank=True, help_text='이 빌딩의 이름은 무엇입니까?')
    owner = models.CharField(max_length=20, blank=True, help_text='이 빌딩은 누구의 소유입니까?')
    construction_date = models.DateField(help_text='이 빌딩의 준공일은 언제입니까?')
    total_area = models.DecimalField(max_digits=20, decimal_places=2, help_text='빌딩의 연면적을 입방미터(m2) 기준으로 기재하세요.(필수)')
    rentable_area = models.DecimalField(max_digits=20, decimal_places=2, blank=True, help_text='빌딩의 실제 임대가능면적을 입방미터(m2) 기준으로 기재하세요.')

    WALL_CHOICES = (
        ('GL', '유리'), # glass
        ('BR', '벽돌'), # brick
        ('CO', '콘크리트'), # concrete
        ('ET', '기타'), # et cetera(etc)
        )
    wall = models.CharField(max_length=10, choices=WALL_CHOICES, default='CO', help_text='외벽의 주된 재질이 무엇입니까?(필수)')

    SOURCE_CHOICES = (
            ('EL', '전기'), # electricity
            ('GA', '가스'), # gas
            ('HP', '폐열히트펌프'), # heat pump
            ('DT', '지역냉난방'), # district
            ('ET', '기타'), # et cetera(etc)
            )
    cooling_source = models.CharField(max_length=10, choices=SOURCE_CHOICES, default='elec', help_text='냉방에 주로 어떤 에너지를 사용합니까?(필수)')
    heating_source = models.CharField(max_length=10, choices=SOURCE_CHOICES, default='gas', help_text='난방에 주로 어떤 에너지를 사용합니까?(필수)')

    ismart_id = models.CharField(_('Kepco iSmart ID'), max_length=20, unique=True, help_text='한전 iSmart ID를 기재하세요.(필수)')
    ismart_pw = models.CharField(_('Kepco iSmart PW'), max_length=20, help_text='한전 iSmart PW를 기재하세요.(필수)')
    fm = models.CharField(_('Facility Management'), max_length=20, blank=True, help_text='이 빌딩의 시설관리회사는 어디입니까?')
    photo = models.ImageField(_('Building Photo'), blank=True, null=True, upload_to=get_image_filename)
    registration = models.DateTimeField(default=timezone.now)

    def __str__(self):
        return self.name

    @register.filter
    def to_class_name(self, value):
        return value.__class__.__name__


class Ismart(models.Model):
    building = models.ForeignKey(Building, on_delete=models.CASCADE)
    datetime = models.DateTimeField()
    kWh = models.FloatField()
    kW_peak = models.FloatField()
    kVarh_lag = models.FloatField()
    kVarh_lead = models.FloatField()
    tCO2 = models.FloatField()
    pf_lag = models.FloatField()
    pf_lead = models.FloatField()

    class Meta:
        unique_together = ('building', 'datetime')

    # def __str__(self):
    #     title = str(self.building)+str('_')+str(self.datetime)
    #     return title

    @register.filter
    def to_class_name(self, value):
        return value.__class__.__name__


class Analysis(models.Model):
    building = models.ForeignKey(Building, on_delete=models.CASCADE)
    elec_use_workingday = models.FloatField(verbose_name='사용일 평균 전력량')
    elec_use_holiday = models.FloatField(verbose_name='휴일 평균 전력량')
    baseload = models.FloatField(verbose_name='사용일 평균 기저부하')
    coolingload = models.FloatField(verbose_name='여름철 사용일 평균 냉방부하')
    cooling_coef = models.FloatField(verbose_name='여름철 사용일 평균 냉방계수')
    heatingload = models.FloatField(verbose_name='겨울철 사용일 평균 난방부하')
    heating_coef = models.FloatField(verbose_name='겨울철 사용일 평균 난방계수')
    balance_point = models.FloatField()
    saving_potential = models.FloatField(verbose_name='전력 예상 절감율')
    registration = models.TimeField(default=timezone.now)

    class Meta:
        verbose_name_plural = "Analysis"

    def __str__(self):
        return str(self.building)

    
