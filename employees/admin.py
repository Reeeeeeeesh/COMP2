from django.contrib import admin
from .models import (
    Employee, 
    HistoricalPerformance, 
    Team, 
    TeamRevenue, 
    SalaryBand, 
    MeritMatrix, 
    KpiAchievement, 
    RevenueTrendFactor
)

# Register your models here.

admin.site.register(Employee)
admin.site.register(HistoricalPerformance)
admin.site.register(Team)
admin.site.register(TeamRevenue)
admin.site.register(SalaryBand)
admin.site.register(MeritMatrix)
admin.site.register(KpiAchievement)
admin.site.register(RevenueTrendFactor)
