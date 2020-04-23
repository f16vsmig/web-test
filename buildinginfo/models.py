from django.db import models
from django.utils.translation import gettext as _
from django.utils.text import slugify
from django.utils import timezone
from django.conf import settings
from django import template
from django.dispatch import receiver
import os

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
    weather_station = models.ForeignKey(
        WeatherStation, on_delete=models.PROTECT)
    datetime = models.DateTimeField(null=True, blank=True, default=None)
    temp = models.FloatField(null=True, blank=True, default=None)
    rain = models.FloatField(null=True, blank=True, default=None)
    wind = models.FloatField(null=True, blank=True, default=None)
    wind_direction = models.IntegerField(null=True, blank=True, default=None)
    humidity = models.IntegerField(null=True, blank=True, default=None)
    vapor_pressure = models.FloatField(null=True, blank=True, default=None)
    dewpoint = models.FloatField(null=True, blank=True, default=None)
    field_elecation_pressure = models.FloatField(
        null=True, blank=True, default=None)
    sealevel_pressure = models.FloatField(null=True, blank=True, default=None)
    daylight_hours = models.FloatField(null=True, blank=True, default=None)
    irradiation_amount = models.FloatField(null=True, blank=True, default=None)
    snowfall_amount = models.FloatField(null=True, blank=True, default=None)
    snowfall_3h = models.FloatField(null=True, blank=True, default=None)
    cloud_total = models.IntegerField(null=True, blank=True, default=None)
    cloud_lower = models.IntegerField(null=True, blank=True, default=None)
    cloud_shape = models.CharField(
        max_length=10, null=True, blank=True, default=None)
    cloud_ft = models.IntegerField(null=True, blank=True, default=None)
    visibility = models.IntegerField(null=True, blank=True, default=None)
    WMO_code = models.IntegerField(null=True, blank=True, default=None)
    phenomenon_no = models.CharField(
        max_length=50, null=True, blank=True, default=None)
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
    weather_station = models.ForeignKey(
        WeatherStation, on_delete=models.PROTECT)
    name = models.CharField(max_length=20, unique=True, blank=True,
                            help_text='이 빌딩의 이름은 무엇입니까?')
    owner = models.CharField(max_length=20, blank=True,
                             help_text='이 빌딩은 누구의 소유입니까?')

    USE_CHOICES = (
        ('OFF', '오피스'),
        ('HOS', '병원'),
        ('COM', '상업'),
        ('SCH', '학교'),
        ('COP', '복합'),
        ('RES', '주거'),
    )
    use = models.CharField(max_length=10, choices=USE_CHOICES,
                           default='OFF', help_text='빌딩 용도가 무엇입니까?(필수)')
    construction_date = models.DateField(help_text='이 빌딩의 준공일은 언제입니까?')
    total_area = models.DecimalField(
        max_digits=20, decimal_places=2, help_text='빌딩의 연면적을 입방미터(m2) 기준으로 기재하세요.(필수)')
    rentable_area = models.DecimalField(
        max_digits=20, decimal_places=2, blank=True, help_text='빌딩의 실제 임대가능면적을 입방미터(m2) 기준으로 기재하세요.')

    WALL_CHOICES = (
        ('GL', '유리'),  # glass
        ('BR', '벽돌'),  # brick
        ('CO', '콘크리트'),  # concrete
        ('ET', '기타'),  # et cetera(etc)
    )
    wall = models.CharField(max_length=10, choices=WALL_CHOICES,
                            default='CO', help_text='외벽의 주된 재질이 무엇입니까?(필수)')

    SOURCE_CHOICES = (
        ('EL', '전기'),  # electricity
        ('GA', '가스'),  # gas
        ('HP', '폐열히트펌프'),  # heat pump
        ('DT', '지역냉난방'),  # district
        ('ET', '기타'),  # et cetera(etc)
    )
    cooling_source = models.CharField(
        max_length=10, choices=SOURCE_CHOICES, default='elec', help_text='냉방에 주로 어떤 에너지를 사용합니까?(필수)')
    heating_source = models.CharField(
        max_length=10, choices=SOURCE_CHOICES, default='gas', help_text='난방에 주로 어떤 에너지를 사용합니까?(필수)')

    ismart_id = models.CharField(
        _('Kepco iSmart ID'), max_length=20, unique=True, help_text='한전 iSmart ID를 기재하세요.(필수)')
    ismart_pw = models.CharField(
        _('Kepco iSmart PW'), max_length=20, help_text='한전 iSmart PW를 기재하세요.(필수)')
    fm = models.CharField(_('Facility Management'), max_length=20,
                          blank=True, help_text='이 빌딩의 시설관리회사는 어디입니까?')
    photo = models.ImageField(
        _('Building Photo'), blank=True, null=True, upload_to=get_image_filename)
    registration = models.DateTimeField(default=timezone.now)

    def __str__(self):
        return self.name

    @register.filter
    def to_class_name(self, value):
        return value.__class__.__name__


### 모델 데이터 삭제시 연결된 파일도 삭제 ###
@receiver(models.signals.post_delete, sender=Building)
def auto_delete_file_on_delete(sender, instance, **kwargs):
    """
    Deletes file from filesystem
    when corresponding `MediaFile` object is deleted.
    """
    if instance.photo:
        if os.path.isfile(instance.photo.path):
            os.remove(instance.photo.path)


### 모델 데이터 변경시 기존 파일 삭제 ###
@receiver(models.signals.pre_save, sender=Building)
def auto_delete_file_on_change(sender, instance, **kwargs):
    """
    Deletes old file from filesystem
    when corresponding `MediaFile` object is updated
    with new file.
    """
    if not instance.pk:
        return False

    try:
        old_file = sender.objects.get(pk=instance.pk).photo
    except sender.DoesNotExist:
        return False

    new_file = instance.photo
    if old_file and old_file != new_file:
        if os.path.isfile(old_file.path):
            os.remove(old_file.path)


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
    baseload_workingday = models.FloatField(
        verbose_name='평일 기초 사용량', default=None, null=True)
    baseload_holiday = models.FloatField(
        verbose_name='휴일 기초 사용량', default=None, null=True)
    balance_point = models.FloatField(verbose_name='밸런스포인트')
    saving_potential = models.FloatField(verbose_name='예상 절감율')
    registration = models.DateTimeField(default=timezone.now)

    class Meta:
        verbose_name_plural = "Analysis"

    def __str__(self):
        return str(self.building)


class EquipmentList(models.Model):
    name = models.CharField(max_length=30, verbose_name='장비명')
    type = models.CharField(max_length=30, verbose_name='형식')
    desc = models.TextField(blank=True, verbose_name='설명')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        sign = '{0}({1})'
        return sign.format(self.name, self.type)


class SpecList(models.Model):
    equip = models.ForeignKey(
        EquipmentList, on_delete=models.CASCADE, verbose_name='장비')
    name = models.CharField(max_length=30, verbose_name='스펙명')
    unit = models.CharField(max_length=30, verbose_name='단위')
    desc = models.TextField(blank=True, verbose_name='설명')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        sign = '{0}-{1}({2})'
        return sign.format(self.equip, self.name, self.unit)


class Facility(models.Model):
    building = models.ForeignKey(Building, on_delete=models.CASCADE)
    equip = models.ForeignKey(EquipmentList, on_delete=models.PROTECT)
    name = models.CharField(max_length=50)
    connect = models.ManyToManyField(
        'self', blank=True, through='FacilityRelation', symmetrical=False, related_name='+')
    memo = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        sign = '{0}-{1}'
        return sign.format(self.equip, self.name)


class FacilityRelation(models.Model):
    primary = models.ForeignKey(
        Facility, on_delete=models.CASCADE, related_name='from_equip')
    secondary = models.ForeignKey(
        Facility, on_delete=models.CASCADE, related_name='to_equip')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        sign = 'building: {0}, primary: {1}, secondary: {2}'
        return sign.format(self.primary.building, self.primary, self.secondary)


class Spec(models.Model):
    facility = models.ForeignKey(Facility, on_delete=models.CASCADE)
    spec = models.ForeignKey(SpecList, on_delete=models.PROTECT)
    value = models.FloatField()
    memo = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        sign = '{0}-{1}-{2}'
        return sign.format(self.facility.building, self.facility, self.spec)


class DatapointList(models.Model):
    equip = models.ForeignKey(
        EquipmentList, on_delete=models.CASCADE, verbose_name='장비')
    name = models.CharField(max_length=30, verbose_name='포인트명')
    unit = models.CharField(max_length=30, verbose_name='단위')
    desc = models.TextField(blank=True, verbose_name='설명')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        sign = '{0}-{1}-{2}({3})'
        return sign.format(self.equip.building, self.equip, self.name, self.unit)


class Datapoint(models.Model):
    facility = models.ForeignKey(Facility, on_delete=models.CASCADE)
    point = models.ForeignKey(DatapointList, on_delete=models.PROTECT)
    desc = models.TextField(blank=True, verbose_name='설명')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        sign = '{0}-{1}'
        return sign.format(self.facility, self.point)


class DatapointLog(models.Model):
    point = models.ForeignKey(Datapoint, on_delete=models.CASCADE)
    timestamp = models.DateTimeField()
    value = models.FloatField()
