from django.contrib import admin
from .models import Building, Ismart, Weather, WeatherStation, Analysis

@admin.register(Building)
class BuildingAdmin(admin.ModelAdmin):
    list_display = ['name', 'owner', 'weather_station', 'construction_date', 'total_area', 'registration']
    list_display_links = ['name']
    list_filter = ['name', 'owner', 'weather_station']

@admin.register(Ismart)
class IsmartAdmin(admin.ModelAdmin):
    list_display = ['building', 'datetime', 'kWh', 'kW_peak', 'tCO2']
    list_display_links = ['datetime']
    list_filter = ['building']

@admin.register(Weather)
class WeatherAdmin(admin.ModelAdmin):
    list_display = ['weather_station', 'datetime', 'temp', 'humidity', 'rain']
    list_display_links = ['datetime']
    list_filter = ['weather_station']

@admin.register(WeatherStation)
class WeatherStationAdmin(admin.ModelAdmin):
    list_display = ['city', 'station_id']
    list_display_links = ['station_id']

@admin.register(Analysis)
class AnalysisAdmin(admin.ModelAdmin):
    list_display = ['building', 'registration']
    list_filter = ['building']

# @admin.register(BenchmarkResult)
# class BenchmarkResultAdmin(admin.ModelAdmin):
#     list_display = ['building', 'annual_use_rank']
#     list_filter = ['building']