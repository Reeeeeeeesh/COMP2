"""
Test script for the simulate endpoint.
Run with: python test_simulate.py
"""
import os
import json
import requests

# Set up Django environment
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'compensation_tool.settings')

# Test data
test_data = {
    "employees": [
        {
            "name": "John Analyst",
            "employee_id": "A001",
            "base_salary": "80000.00",
            "pool_share": "0.05",
            "target_bonus": "10000.00",
            "performance_score": "0.85",
            "last_year_revenue": "500000.00",
            "role": "Analyst",
            "level": 1,
            "team": "Investment",
            "performance_rating": "Meets Expectations",
            "is_mrt": False
        },
        {
            "name": "Jane Manager",
            "employee_id": "M001",
            "base_salary": "120000.00",
            "pool_share": "0.10",
            "target_bonus": "30000.00",
            "performance_score": "0.90",
            "last_year_revenue": "1000000.00",
            "role": "Manager",
            "level": 3,
            "team": "Trading",
            "performance_rating": "Exceeds Expectations",
            "is_mrt": True
        }
    ],
    "config": {
        "revenue_delta": "0.05",
        "adjustment_factor": "1.0",
        "use_pool_method": False,
        "use_proposed_model": True,
        "current_year": 2025,
        "performance_rating": "Meets Expectations",
        "is_mrt": False,
        "use_overrides": True
    }
}

def main():
    """Run the test."""
    print("Starting test...")
    
    # First, make sure the Django server is running
    try:
        # Make a request to the simulate endpoint
        response = requests.post(
            'http://localhost:8000/api/simulate/',
            json=test_data,
            headers={'Content-Type': 'application/json'}
        )
        
        # Print the response
        print(f"Status code: {response.status_code}")
        if response.status_code == 200:
            print("Success!")
            result = response.json()
            print(f"Results count: {len(result.get('results', []))}")
            print(f"Summary: {result.get('summary', {})}")
        else:
            print(f"Error: {response.text}")
            
    except Exception as e:
        print(f"Error: {e}")
    
    print("Test complete.")

if __name__ == "__main__":
    main()
