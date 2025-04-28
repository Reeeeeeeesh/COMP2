from django.db import models

# Create your models here.

class CompensationConfig(models.Model):
    """Configuration presets for compensation calculations"""
    name = models.CharField(max_length=100)
    description = models.TextField(blank=True)
    base_multiplier = models.DecimalField(max_digits=5, decimal_places=2, default=1.0)
    performance_weight = models.DecimalField(max_digits=3, decimal_places=2, default=0.4)
    revenue_weight = models.DecimalField(max_digits=3, decimal_places=2, default=0.6)
    min_bonus_percent = models.DecimalField(max_digits=5, decimal_places=2, default=0)
    max_bonus_percent = models.DecimalField(max_digits=5, decimal_places=2, default=200)
    is_active = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def save(self, *args, **kwargs):
        if self.is_active:
            # Set all other configs to inactive
            CompensationConfig.objects.all().update(is_active=False)
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.name} {'(Active)' if self.is_active else ''}"

class Employee(models.Model):
    employee_id = models.IntegerField(unique=True, null=True, blank=True)
    name = models.CharField(max_length=100)
    base_salary = models.DecimalField(max_digits=12, decimal_places=2)
    pool_share = models.DecimalField(max_digits=5, decimal_places=4, help_text="Fraction of revenue (0–1)")
    target_bonus = models.DecimalField(max_digits=12, decimal_places=2)
    performance_score = models.DecimalField(max_digits=5, decimal_places=4, help_text="0–1")
    last_year_revenue = models.DecimalField(max_digits=15, decimal_places=2)
    # New fields for enhanced compensation model
    role = models.CharField(max_length=100, blank=True, null=True, help_text="Job title/function")
    level = models.CharField(max_length=50, blank=True, null=True, help_text="Seniority level")
    is_mrt = models.BooleanField(default=False, help_text="Material Risk Taker flag")
    performance_rating = models.CharField(max_length=50, blank=True, null=True, 
                                         help_text="E.g., 'Exceeds Expectations', 'Meets Expectations'")
    team = models.ForeignKey('Team', on_delete=models.SET_NULL, null=True, blank=True, related_name='members')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        if self.employee_id:
            return f"{self.employee_id} - {self.name}"
        return self.name

    @property
    def compa_ratio(self):
        """Calculate compa-ratio if salary band exists"""
        try:
            band = SalaryBand.objects.get(role=self.role, level=self.level)
            if band.mid_value:
                return float(self.base_salary) / float(band.mid_value)
            return None
        except SalaryBand.DoesNotExist:
            return None

class HistoricalPerformance(models.Model):
    employee = models.ForeignKey(Employee, on_delete=models.CASCADE, related_name="history")
    year = models.IntegerField()
    revenue = models.DecimalField(max_digits=15, decimal_places=2)
    performance_score = models.DecimalField(max_digits=5, decimal_places=4)

    class Meta:
        unique_together = ("employee", "year")

class Team(models.Model):
    """Team grouping for employees"""
    name = models.CharField(max_length=100)
    
    def __str__(self):
        return self.name

class TeamRevenue(models.Model):
    """Annual revenue records for teams"""
    team = models.ForeignKey(Team, on_delete=models.CASCADE, related_name='revenues')
    year = models.IntegerField()
    revenue = models.DecimalField(max_digits=15, decimal_places=2)
    
    class Meta:
        unique_together = ('team', 'year')
        
    def __str__(self):
        return f"{self.team.name} - {self.year}: {self.revenue}"

class SalaryBand(models.Model):
    """Salary bands by role and level"""
    role = models.CharField(max_length=100)
    level = models.CharField(max_length=50)
    min_value = models.DecimalField(max_digits=12, decimal_places=2)
    mid_value = models.DecimalField(max_digits=12, decimal_places=2)
    max_value = models.DecimalField(max_digits=12, decimal_places=2)
    
    class Meta:
        unique_together = ('role', 'level')
        
    def __str__(self):
        return f"{self.role} - {self.level}"

class MeritMatrix(models.Model):
    """Merit increase matrix values"""
    performance_rating = models.CharField(max_length=50)
    compa_ratio_range = models.CharField(max_length=50, help_text="E.g., 'Q1', 'Q2', 'Q3', 'Q4'")
    increase_percentage = models.DecimalField(max_digits=5, decimal_places=4)
    
    class Meta:
        unique_together = ('performance_rating', 'compa_ratio_range')
        
    def __str__(self):
        return f"{self.performance_rating} - {self.compa_ratio_range}: {self.increase_percentage}"

class KpiAchievement(models.Model):
    """KPI achievement tracking"""
    employee = models.ForeignKey(Employee, on_delete=models.CASCADE, related_name='kpi_achievements')
    year = models.IntegerField()
    investment_performance = models.DecimalField(max_digits=5, decimal_places=4, help_text="Achievement percentage")
    risk_management = models.DecimalField(max_digits=5, decimal_places=4, help_text="Achievement percentage")
    aum_revenue = models.DecimalField(max_digits=5, decimal_places=4, help_text="Achievement percentage")
    qualitative = models.DecimalField(max_digits=5, decimal_places=4, help_text="Achievement percentage")
    
    class Meta:
        unique_together = ('employee', 'year')
        
    def __str__(self):
        return f"{self.employee.name} - {self.year}"

class RevenueTrendFactor(models.Model):
    """Revenue trend adjustment factors"""
    trend_category = models.CharField(max_length=50, help_text="E.g., 'Strong Growth', 'Stable', 'Decline'")
    adjustment_factor = models.DecimalField(max_digits=5, decimal_places=4, help_text="Multiplier for merit increase")
    
    def __str__(self):
        return f"{self.trend_category}: {self.adjustment_factor}"

class DataSnapshot(models.Model):
    """Model to store snapshots of all data for baseline scenarios"""
    name = models.CharField(max_length=100)
    description = models.TextField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    created_by = models.CharField(max_length=100, blank=True, null=True)
    is_active = models.BooleanField(default=True)

    def __str__(self):
        return self.name

class EmployeeSnapshot(models.Model):
    """Model to store employee data snapshots"""
    snapshot = models.ForeignKey(DataSnapshot, on_delete=models.CASCADE, related_name='employees')
    employee_id = models.IntegerField(null=True, blank=True)
    name = models.CharField(max_length=100)
    base_salary = models.DecimalField(max_digits=12, decimal_places=2)
    pool_share = models.DecimalField(max_digits=5, decimal_places=4)
    target_bonus = models.DecimalField(max_digits=12, decimal_places=2)
    performance_score = models.DecimalField(max_digits=5, decimal_places=4)
    last_year_revenue = models.DecimalField(max_digits=15, decimal_places=2)
    role = models.CharField(max_length=100, blank=True, null=True)
    level = models.CharField(max_length=50, blank=True, null=True)
    is_mrt = models.BooleanField(default=False)
    performance_rating = models.CharField(max_length=50, blank=True, null=True)
    team = models.IntegerField(null=True, blank=True)  # Store team ID reference
    
    def __str__(self):
        return f"{self.name} (Snapshot: {self.snapshot.name})"

class ConfigSnapshot(models.Model):
    """Model to store configuration data snapshots"""
    snapshot = models.ForeignKey(DataSnapshot, on_delete=models.CASCADE, related_name='configs')
    config_type = models.CharField(max_length=50)  # 'salary_band', 'merit_matrix', etc.
    data = models.JSONField()  # Store the configuration data as JSON
    
    def __str__(self):
        return f"{self.config_type} (Snapshot: {self.snapshot.name})"

class Scenario(models.Model):
    """Model to store compensation scenarios for comparison and analysis"""
    name = models.CharField(max_length=100)
    description = models.TextField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    created_by = models.CharField(max_length=100, blank=True, null=True)
    is_active = models.BooleanField(default=True)
    # Base snapshot to use for this scenario
    base_snapshot = models.ForeignKey(DataSnapshot, on_delete=models.SET_NULL, null=True, blank=True, related_name='scenarios')
    # Scenario parameters
    parameters = models.JSONField(default=dict)
    # Results cache
    results_cache = models.JSONField(null=True, blank=True)
    
    def __str__(self):
        return self.name
        
class ScenarioEmployeeOverride(models.Model):
    """Model to store employee-specific overrides for a scenario"""
    scenario = models.ForeignKey(Scenario, on_delete=models.CASCADE, related_name='employee_overrides')
    employee = models.ForeignKey(Employee, on_delete=models.CASCADE)
    # Override fields
    performance_rating = models.CharField(max_length=50, blank=True, null=True)
    is_mrt = models.BooleanField(null=True, blank=True)
    base_salary_override = models.DecimalField(max_digits=12, decimal_places=2, null=True, blank=True)
    target_bonus_override = models.DecimalField(max_digits=12, decimal_places=2, null=True, blank=True)
    discretionary_adjustment = models.DecimalField(max_digits=5, decimal_places=2, null=True, blank=True, 
                                                 help_text="Percentage adjustment to calculated compensation")
    
    class Meta:
        unique_together = ('scenario', 'employee')
        
    def __str__(self):
        return f"{self.employee.name} override for {self.scenario.name}"

class ScenarioVersion(models.Model):
    """Model to store versions of a scenario for tracking changes over time"""
    scenario = models.ForeignKey(Scenario, on_delete=models.CASCADE, related_name='versions')
    version_number = models.PositiveIntegerField()
    created_at = models.DateTimeField(auto_now_add=True)
    created_by = models.CharField(max_length=100, blank=True, null=True)
    parameters = models.JSONField(default=dict)
    results_cache = models.JSONField(null=True, blank=True)
    notes = models.TextField(blank=True, null=True, help_text="Notes about changes in this version")
    
    class Meta:
        unique_together = ('scenario', 'version_number')
        ordering = ['-version_number']
        
    def __str__(self):
        return f"{self.scenario.name} v{self.version_number}"
        
class ScenarioComparison(models.Model):
    """Model to store comparison configurations between scenarios or versions"""
    name = models.CharField(max_length=100)
    description = models.TextField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    created_by = models.CharField(max_length=100, blank=True, null=True)
    # Scenarios or versions to compare
    primary_scenario = models.ForeignKey(Scenario, on_delete=models.CASCADE, related_name='primary_comparisons')
    primary_version = models.ForeignKey(ScenarioVersion, on_delete=models.SET_NULL, null=True, blank=True, related_name='primary_comparisons')
    comparison_scenarios = models.ManyToManyField(Scenario, related_name='comparison_items', through='ComparisonItem')
    # Results cache
    results_cache = models.JSONField(null=True, blank=True)
    
    def __str__(self):
        return self.name
        
class ComparisonItem(models.Model):
    """Junction model for scenario comparisons"""
    comparison = models.ForeignKey(ScenarioComparison, on_delete=models.CASCADE)
    scenario = models.ForeignKey(Scenario, on_delete=models.CASCADE)
    version = models.ForeignKey(ScenarioVersion, on_delete=models.SET_NULL, null=True, blank=True)
    display_order = models.PositiveIntegerField(default=0)
    
    class Meta:
        ordering = ['display_order']
        unique_together = ('comparison', 'scenario', 'version')
        
    def __str__(self):
        version_str = f" v{self.version.version_number}" if self.version else ""
        return f"{self.scenario.name}{version_str} in {self.comparison.name}"
