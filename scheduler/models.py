from django.db import models
from django.urls import reverse
from buildinginfo.models import Building

class Event(models.Model):
    building = models.ForeignKey(Building, on_delete=models.CASCADE)
    start_time = models.DateTimeField()
    end_time = models.DateTimeField()

    event_options = (
            ('공휴일', '공휴일'),
            ('정기휴일', '정기휴일'),
            ('임시휴일', '임시휴일'),
            ('기타', '기타'),
            )
    event = models.CharField(max_length=10, choices=event_options)
    notes = models.TextField(blank=True, null=True)

    def __str__(self):
        title = str(self.building)+str('_')+str(self.start_time)+str('_')+str(self.end_time)+str('_')+str(self.event_options)
        return title

    # @property
    # def get_html_url(self):
    #     detail_url = reverse('scheduler:event_detail', args=(self.id,))
    #     delete_url = reverse('scheduler:event_delete', args=(self.id,))
    #     return f'<span class="event-header"></span><span class="event pr-2"><a class="popup w-100" href="{detail_url}"><span class="event d-inline-block text-truncate w-75" style="max-width: 85px;">&nbsp;{self.building}-{self.event}&nbsp;</span></a><a class="event-delete" href="{delete_url}" onclick="return confirm(&#39;이 일정을 삭제하시겠습니까?&#39;)"><i class="event-delete fas fa-times text-danger text-right"></i></a></span>'
