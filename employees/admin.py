from django.contrib import admin
from .models import Employee, HistoricalPerformance

# Register your models here.

admin.site.register(Employee)
admin.site.register(HistoricalPerformance)
