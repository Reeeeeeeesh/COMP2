from django.urls import path, include
from rest_framework.routers import DefaultRouter
from . import views

router = DefaultRouter()
router.register(r'salary-bands', views.SalaryBandViewSet)
router.register(r'team-revenues', views.TeamRevenueViewSet)
router.register(r'merit-matrix', views.MeritMatrixViewSet)
router.register(r'revenue-trend-factors', views.RevenueTrendFactorViewSet)
router.register(r'kpi-achievements', views.KpiAchievementViewSet)
router.register(r'teams', views.TeamViewSet)
router.register(r'compensation-configs', views.CompensationConfigViewSet)
router.register(r'employees', views.EmployeeViewSet, basename='employee')
router.register(r'snapshots', views.DataSnapshotViewSet)
router.register(r'scenarios', views.ScenarioViewSet)
router.register(r'scenario-overrides', views.ScenarioEmployeeOverrideViewSet)
router.register(r'scenario-versions', views.ScenarioVersionViewSet)
router.register(r'scenario-comparisons', views.ScenarioComparisonViewSet)
router.register(r'comparison-items', views.ComparisonItemViewSet)

urlpatterns = [
    path('', include(router.urls)),
    path('ping/', views.ping, name='ping'),  # Health check

    # --- Team Management ---
    path('teams/definitive-import/', views.definitive_team_upload, name='definitive-team-import'), # THE ONLY team uploader
    path('inspect-csv/', views.inspect_csv_file, name='inspect-csv-file'), # Inspector tool
    
    # --- Configuration Model Upload Endpoints ---
    path('salary-bands/upload/', views.SalaryBandUploadView.as_view(), name='salaryband-upload'),
    path('team-revenues/upload/', views.TeamRevenueUploadView.as_view(), name='teamrevenue-upload'),
    path('merit-matrices/upload/', views.MeritMatrixUploadView.as_view(), name='meritmatrix-upload'),
    path('revenue-trend-factors/upload/', views.RevenueTrendFactorUploadView.as_view(), name='revenuetrendfactor-upload'),
    path('kpi-achievements/upload/', views.KpiAchievementUploadView.as_view(), name='kpiachievement-upload'),
    # Bulk upload all configuration sections
    path('config-bulk-upload/', views.ConfigBulkUploadView.as_view(), name='config-bulk-upload'),
    path('debug-config-upload/', views.debug_config_upload, name='debug-config-upload'),
    # Snapshot endpoints
    path('snapshots/create/', views.create_snapshot, name='create-snapshot'),
    path('snapshots/<int:snapshot_id>/restore/', views.restore_snapshot, name='restore-snapshot'),
    # Basic endpoints
    path('upload-data/', views.upload_data, name='upload-data'),
    path('debug-upload/', views.debug_upload, name='debug-upload'),
    path('debug-salary-bands/', views.debug_salary_bands, name='debug-salary-bands'),
    path('debug-merit-matrix/', views.debug_merit_matrix, name='debug-merit-matrix'),
    path('calculate/', views.calculate, name='calculate'),
    path('simulate/', views.simulate, name='simulate'),
]
