from rest_framework import serializers
from .models import Employee, SalaryBand, TeamRevenue, MeritMatrix, RevenueTrendFactor, KpiAchievement

class EmployeeSerializer(serializers.ModelSerializer):
    class Meta:
        model = Employee
        fields = '__all__'  # id, name, base_salary, pool_share, target_bonus, performance_score, last_year_revenue, timestamps

# Configuration serializers
class SalaryBandSerializer(serializers.ModelSerializer):
    class Meta:
        model = SalaryBand
        fields = '__all__'

class TeamRevenueSerializer(serializers.ModelSerializer):
    class Meta:
        model = TeamRevenue
        fields = '__all__'

class MeritMatrixSerializer(serializers.ModelSerializer):
    class Meta:
        model = MeritMatrix
        fields = '__all__'

class RevenueTrendFactorSerializer(serializers.ModelSerializer):
    class Meta:
        model = RevenueTrendFactor
        fields = '__all__'

class KpiAchievementSerializer(serializers.ModelSerializer):
    class Meta:
        model = KpiAchievement
        fields = '__all__'
