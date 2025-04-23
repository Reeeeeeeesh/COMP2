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
