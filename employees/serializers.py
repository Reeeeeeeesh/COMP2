from rest_framework import serializers
from .models import Employee

class EmployeeSerializer(serializers.ModelSerializer):
    class Meta:
        model = Employee
        fields = '__all__'  # id, name, base_salary, pool_share, target_bonus, performance_score, last_year_revenue, timestamps
