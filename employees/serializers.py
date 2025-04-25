from rest_framework import serializers
from .models import Employee, CompensationConfig, Team, TeamRevenue, SalaryBand, MeritMatrix, KpiAchievement, RevenueTrendFactor, DataSnapshot, EmployeeSnapshot, ConfigSnapshot

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

# Add TeamSerializer
class TeamSerializer(serializers.ModelSerializer):
    class Meta:
        model = Team
        fields = '__all__'

# Snapshot serializers
class EmployeeSnapshotSerializer(serializers.ModelSerializer):
    class Meta:
        model = EmployeeSnapshot
        fields = '__all__'

class ConfigSnapshotSerializer(serializers.ModelSerializer):
    class Meta:
        model = ConfigSnapshot
        fields = '__all__'

class DataSnapshotSerializer(serializers.ModelSerializer):
    employees = EmployeeSnapshotSerializer(many=True, read_only=True)
    configs = ConfigSnapshotSerializer(many=True, read_only=True)
    
    class Meta:
        model = DataSnapshot
        fields = ['id', 'name', 'description', 'created_at', 'created_by', 'is_active', 'employees', 'configs']

class DataSnapshotCreateSerializer(serializers.ModelSerializer):
    class Meta:
        model = DataSnapshot
        fields = ['name', 'description', 'created_by']
