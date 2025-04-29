import os
import django
import sys

# Set up Django environment
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'compensation_tool.settings')
django.setup()

from django.db import transaction
from employees.models import Employee
from collections import defaultdict

def cleanup_duplicates():
    print("Starting duplicate employee cleanup...")
    
    # Get all employees
    all_employees = Employee.objects.all()
    print(f"Total employees before cleanup: {all_employees.count()}")
    
    # Group employees by name
    employees_by_name = defaultdict(list)
    for emp in all_employees:
        employees_by_name[emp.name].append(emp)
    
    # Find duplicates
    duplicates = {name: emps for name, emps in employees_by_name.items() if len(emps) > 1}
    print(f"Found {len(duplicates)} employees with duplicates")
    
    # Process duplicates
    with transaction.atomic():
        deleted_count = 0
        for name, dupes in duplicates.items():
            print(f"\nProcessing duplicates for: {name}")
            
            # Sort by employee_id (keep ones with ID), then by created_at (keep newest)
            sorted_dupes = sorted(dupes, 
                                 key=lambda e: (e.employee_id is None, 
                                               -e.created_at.timestamp() if e.created_at else 0))
            
            # Keep the first one (has ID or is newest)
            keep = sorted_dupes[0]
            print(f"  Keeping: ID={keep.employee_id}, Created={keep.created_at}")
            
            # Delete the rest
            for dupe in sorted_dupes[1:]:
                print(f"  Deleting: ID={dupe.employee_id}, Created={dupe.created_at}")
                dupe.delete()
                deleted_count += 1
    
    # Final count
    remaining = Employee.objects.count()
    print(f"\nCleanup complete. Deleted {deleted_count} duplicate employees.")
    print(f"Remaining employees: {remaining}")
    
    return deleted_count

if __name__ == "__main__":
    cleanup_duplicates()
