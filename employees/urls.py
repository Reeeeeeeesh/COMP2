from django.urls import path, include
from .views import ping, upload_data, employees_list, calculate, \
    SalaryBandViewSet, TeamRevenueViewSet, MeritMatrixViewSet, RevenueTrendFactorViewSet, KpiAchievementViewSet, CompensationConfigViewSet, \
    TeamUploadView, SalaryBandUploadView, TeamRevenueUploadView, MeritMatrixUploadView, RevenueTrendFactorUploadView, KpiAchievementUploadView, ConfigBulkUploadView, \
    DataSnapshotViewSet, create_snapshot, restore_snapshot, TeamViewSet
from rest_framework.routers import DefaultRouter

router = DefaultRouter()
router.register(r'salary-bands', SalaryBandViewSet)
router.register(r'team-revenues', TeamRevenueViewSet)
router.register(r'merit-matrices', MeritMatrixViewSet)
router.register(r'revenue-trend-factors', RevenueTrendFactorViewSet)
router.register(r'kpi-achievements', KpiAchievementViewSet)
router.register(r'compensation-configs', CompensationConfigViewSet)
router.register(r'snapshots', DataSnapshotViewSet)
router.register(r'teams', TeamViewSet)

urlpatterns = [
    # CSV upload for Team master data
    path('teams/upload/', TeamUploadView.as_view(), name='team-upload'),
    # Bulk CSV upload endpoints for configuration models
    path('salary-bands/upload/', SalaryBandUploadView.as_view(), name='salaryband-upload'),
    path('team-revenues/upload/', TeamRevenueUploadView.as_view(), name='teamrevenue-upload'),
    path('merit-matrices/upload/', MeritMatrixUploadView.as_view(), name='meritmatrix-upload'),
    path('revenue-trend-factors/upload/', RevenueTrendFactorUploadView.as_view(), name='revenuetrendfactor-upload'),
    path('kpi-achievements/upload/', KpiAchievementUploadView.as_view(), name='kpiachievement-upload'),
    # Bulk upload all configuration sections
    path('config-bulk-upload/', ConfigBulkUploadView.as_view(), name='config-bulk-upload'),
    # Snapshot endpoints
    path('snapshots/create/', create_snapshot, name='create-snapshot'),
    path('snapshots/<int:snapshot_id>/restore/', restore_snapshot, name='restore-snapshot'),
    # Basic endpoints
    path('ping/', ping, name='api-ping'),
    path('upload-data/', upload_data, name='upload-data'),
    path('employees/', employees_list, name='employees-list'),
    path('calculate/', calculate, name='calculate'),
    path('', include(router.urls)),
]
