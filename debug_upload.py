import os
import django
import csv
from decimal import Decimal

# Set up Django environment
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "compensation_tool.settings")
django.setup()

from employees.models import Employee

# First, print current data in database
print("Current data in database:")
for emp in Employee.objects.all()[:5]:  # Show first 5 for brevity
    print(f"{emp.name}: rating={emp.performance_rating}, mrt={emp.is_mrt}, role={emp.role}")

# Create a test CSV file
TEST_CSV = """name,base_salary,pool_share,target_bonus,performance_score,last_year_revenue,role,level,is_mrt,performance_rating
Test Manager 1,100000,0.05,20000,0.8,500000,Fund Manager,Junior,FALSE,Exceeds Expectations
Test Manager 2,120000,0.06,25000,0.7,600000,Fund Manager,Mid,TRUE,Meets Expectations
Test Manager 3,150000,0.07,30000,0.6,700000,Fund Manager,Senior,FALSE,Below Expectations"""

with open("test_upload.csv", "w") as f:
    f.write(TEST_CSV)

print("\nCreated test CSV file with 3 employees, each with different performance ratings")

# Simulate file upload processing
print("\nProcessing test CSV...")
reader = csv.DictReader(TEST_CSV.splitlines())
for row in reader:
    print(f"Row data: {row}")
    data = {
        'base_salary': Decimal(row['base_salary']),
        'pool_share': Decimal(row['pool_share']),
        'target_bonus': Decimal(row['target_bonus']),
        'performance_score': Decimal(row['performance_score']),
        'last_year_revenue': Decimal(row['last_year_revenue']),
        'role': row.get('role'),
        'level': row.get('level'),
        'is_mrt': row.get('is_mrt', '').lower() == 'true',
        'performance_rating': row.get('performance_rating'),
    }
    print(f"Processed data: {data}")
    emp, created = Employee.objects.update_or_create(name=row['name'], defaults=data)
    print(f"Created/Updated {emp.name}: rating={emp.performance_rating}, mrt={emp.is_mrt}")

# Verify data was saved correctly
print("\nVerifying data after upload:")
for emp in Employee.objects.filter(name__startswith="Test Manager"):
    print(f"{emp.name}: rating={emp.performance_rating}, mrt={emp.is_mrt}, role={emp.role}")
