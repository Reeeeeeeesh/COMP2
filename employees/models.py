from django.db import models

# Create your models here.

class Employee(models.Model):
    name = models.CharField(max_length=100)
    base_salary = models.DecimalField(max_digits=12, decimal_places=2)
    pool_share = models.DecimalField(max_digits=5, decimal_places=4, help_text="Fraction of revenue (0–1)")
    target_bonus = models.DecimalField(max_digits=12, decimal_places=2)
    performance_score = models.DecimalField(max_digits=5, decimal_places=4, help_text="0–1")
    last_year_revenue = models.DecimalField(max_digits=15, decimal_places=2)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.name

class HistoricalPerformance(models.Model):
    employee = models.ForeignKey(Employee, on_delete=models.CASCADE, related_name="history")
    year = models.IntegerField()
    revenue = models.DecimalField(max_digits=15, decimal_places=2)
    performance_score = models.DecimalField(max_digits=5, decimal_places=4)

    class Meta:
        unique_together = ("employee", "year")
