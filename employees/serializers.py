from rest_framework import serializers
from .models import Employee, SalaryBand, TeamRevenue, MeritMatrix, RevenueTrendFactor, KpiAchievement, CompensationConfig

class EmployeeSerializer(serializers.ModelSerializer):
    class Meta:
        model = Employee
        fields = ['id', 'employee_id', 'name', 'base_salary', 'pool_share', 'target_bonus', 
                 'performance_score', 'last_year_revenue', 'role', 'level', 'is_mrt', 
                 'performance_rating', 'team']
        
    def create(self, validated_data):
        # If an employee with this employee_id exists, update it instead of creating new
        employee_id = validated_data.get('employee_id')
        if employee_id:
            employee, created = Employee.objects.update_or_create(
                employee_id=employee_id,
                defaults=validated_data
            )
            return employee
        return super().create(validated_data)

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

class CompensationConfigSerializer(serializers.ModelSerializer):
    class Meta:
        model = CompensationConfig
        fields = '__all__'
