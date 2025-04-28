from rest_framework import serializers
from .dynamic_fields import DynamicFieldsMixin
from .models import Employee, CompensationConfig, Team, TeamRevenue, SalaryBand, MeritMatrix, KpiAchievement, RevenueTrendFactor, DataSnapshot, EmployeeSnapshot, ConfigSnapshot, Scenario, ScenarioEmployeeOverride, ScenarioVersion, ScenarioComparison, ComparisonItem

class EmployeeSerializer(DynamicFieldsMixin, serializers.ModelSerializer):
    # Override decimal fields to handle float values safely
    base_salary = serializers.DecimalField(max_digits=10, decimal_places=2, coerce_to_string=False)
    pool_share = serializers.DecimalField(max_digits=5, decimal_places=4, coerce_to_string=False)
    target_bonus = serializers.DecimalField(max_digits=10, decimal_places=2, coerce_to_string=False)
    performance_score = serializers.DecimalField(max_digits=5, decimal_places=4, coerce_to_string=False)
    last_year_revenue = serializers.DecimalField(max_digits=12, decimal_places=2, coerce_to_string=False)
    
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
class SalaryBandSerializer(DynamicFieldsMixin, serializers.ModelSerializer):
    # Override decimal fields to handle float values safely
    min_salary = serializers.DecimalField(max_digits=10, decimal_places=2, coerce_to_string=False)
    max_salary = serializers.DecimalField(max_digits=10, decimal_places=2, coerce_to_string=False)
    
    class Meta:
        model = SalaryBand
        fields = '__all__'

class TeamRevenueSerializer(DynamicFieldsMixin, serializers.ModelSerializer):
    # Override decimal fields to handle float values safely
    revenue = serializers.DecimalField(max_digits=14, decimal_places=2, coerce_to_string=False)
    
    class Meta:
        model = TeamRevenue
        fields = '__all__'

class MeritMatrixSerializer(DynamicFieldsMixin, serializers.ModelSerializer):
    # Override decimal fields to handle float values safely
    merit_increase = serializers.DecimalField(max_digits=5, decimal_places=4, coerce_to_string=False)
    
    class Meta:
        model = MeritMatrix
        fields = '__all__'

class RevenueTrendFactorSerializer(DynamicFieldsMixin, serializers.ModelSerializer):
    # Override decimal fields to handle float values safely
    factor = serializers.DecimalField(max_digits=5, decimal_places=4, coerce_to_string=False)
    
    class Meta:
        model = RevenueTrendFactor
        fields = '__all__'

class KpiAchievementSerializer(DynamicFieldsMixin, serializers.ModelSerializer):
    # Override decimal fields to handle float values safely
    investment_performance = serializers.DecimalField(max_digits=5, decimal_places=4, coerce_to_string=False)
    risk_management = serializers.DecimalField(max_digits=5, decimal_places=4, coerce_to_string=False)
    aum_revenue = serializers.DecimalField(max_digits=5, decimal_places=4, coerce_to_string=False)
    qualitative = serializers.DecimalField(max_digits=5, decimal_places=4, coerce_to_string=False)
    
    class Meta:
        model = KpiAchievement
        fields = '__all__'

class CompensationConfigSerializer(DynamicFieldsMixin, serializers.ModelSerializer):
    class Meta:
        model = CompensationConfig
        fields = '__all__'

# Add TeamSerializer
class TeamSerializer(DynamicFieldsMixin, serializers.ModelSerializer):
    class Meta:
        model = Team
        fields = '__all__'

# Snapshot serializers
class EmployeeSnapshotSerializer(DynamicFieldsMixin, serializers.ModelSerializer):
    class Meta:
        model = EmployeeSnapshot
        fields = '__all__'

class ConfigSnapshotSerializer(DynamicFieldsMixin, serializers.ModelSerializer):
    class Meta:
        model = ConfigSnapshot
        fields = '__all__'

class DataSnapshotSerializer(DynamicFieldsMixin, serializers.ModelSerializer):
    employees = EmployeeSnapshotSerializer(many=True, read_only=True)
    configs = ConfigSnapshotSerializer(many=True, read_only=True)
    
    class Meta:
        model = DataSnapshot
        fields = ['id', 'name', 'description', 'created_at', 'created_by', 'is_active', 'employees', 'configs']

class DataSnapshotCreateSerializer(DynamicFieldsMixin, serializers.ModelSerializer):
    class Meta:
        model = DataSnapshot
        fields = ['name', 'description', 'created_by']

class ScenarioEmployeeOverrideSerializer(DynamicFieldsMixin, serializers.ModelSerializer):
    employee_name = serializers.SerializerMethodField()
    
    class Meta:
        model = ScenarioEmployeeOverride
        fields = '__all__'
    
    def get_employee_name(self, obj):
        return obj.employee.name if obj.employee else None
        
    def to_representation(self, instance):
        ret = super().to_representation(instance)
        # Ensure decimal fields are represented as numbers, not strings
        for field in ['base_salary_override', 'target_bonus_override', 'discretionary_adjustment']:
            if field in ret and ret[field] is not None:
                ret[field] = float(ret[field])
        return ret

class ScenarioSerializer(DynamicFieldsMixin, serializers.ModelSerializer):
    employee_overrides = ScenarioEmployeeOverrideSerializer(many=True, read_only=True)
    base_snapshot_name = serializers.SerializerMethodField()
    version_count = serializers.SerializerMethodField()
    latest_version = serializers.SerializerMethodField()
    
    class Meta:
        model = Scenario
        fields = '__all__'
    
    def get_base_snapshot_name(self, obj):
        return obj.base_snapshot.name if obj.base_snapshot else None
        
    def get_version_count(self, obj):
        return obj.versions.count()
        
    def get_latest_version(self, obj):
        latest = obj.versions.first()
        if latest:
            return {
                'id': latest.id,
                'version_number': latest.version_number,
                'created_at': latest.created_at
            }
        return None

class ScenarioVersionSerializer(DynamicFieldsMixin, serializers.ModelSerializer):
    scenario_name = serializers.SerializerMethodField()
    
    class Meta:
        model = ScenarioVersion
        fields = '__all__'
        
    def get_scenario_name(self, obj):
        return obj.scenario.name if obj.scenario else None

class ComparisonItemSerializer(DynamicFieldsMixin, serializers.ModelSerializer):
    scenario_name = serializers.SerializerMethodField()
    version_number = serializers.SerializerMethodField()
    
    class Meta:
        model = ComparisonItem
        fields = '__all__'
        
    def get_scenario_name(self, obj):
        return obj.scenario.name if obj.scenario else None
        
    def get_version_number(self, obj):
        return obj.version.version_number if obj.version else None

class ScenarioComparisonSerializer(DynamicFieldsMixin, serializers.ModelSerializer):
    comparison_items = ComparisonItemSerializer(source='comparisonitem_set', many=True, read_only=True)
    primary_scenario_name = serializers.SerializerMethodField()
    primary_version_number = serializers.SerializerMethodField()
    
    class Meta:
        model = ScenarioComparison
        fields = '__all__'
        
    def get_primary_scenario_name(self, obj):
        return obj.primary_scenario.name if obj.primary_scenario else None
        
    def get_primary_version_number(self, obj):
        return obj.primary_version.version_number if obj.primary_version else None
