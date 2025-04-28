from decimal import Decimal
from django.test import TestCase
from django.urls import reverse, resolve
from rest_framework.test import APITestCase, APIClient
from .models import Employee
from .compensation_engine import calculate_model_a, run_model_a_for_all, calculate_model_b_pool, calculate_model_b_target, run_model_b_for_all, run_comparison

# Create your tests here.

class ModelATest(TestCase):
    def setUp(self):
        self.emp = Employee.objects.create(
            name='Test',
            base_salary=Decimal('1000.00'),
            pool_share=Decimal('0.0000'),
            target_bonus=Decimal('0.00'),
            performance_score=Decimal('0.0000'),
            last_year_revenue=Decimal('0.00')
        )

    def test_zero_delta(self):
        result = calculate_model_a(self.emp, Decimal('0'), Decimal('1'))
        self.assertEqual(result['adjusted_base'], Decimal('1000.00'))
        self.assertEqual(result['variable_portion'], Decimal('0.00'))
        self.assertFalse(result['capped'])
        self.assertFalse(result['floored'])

    def test_zero_factor(self):
        result = calculate_model_a(self.emp, Decimal('0.1'), Decimal('0'))
        self.assertEqual(result['adjusted_base'], Decimal('1000.00'))
        self.assertEqual(result['variable_portion'], Decimal('0.00'))

    def test_positive_delta_within_limits(self):
        result = calculate_model_a(self.emp, Decimal('0.1'), Decimal('1'))
        self.assertEqual(result['adjusted_base'], Decimal('1100.00'))
        self.assertEqual(result['variable_portion'], Decimal('100.00'))

    def test_hitting_cap(self):
        result = calculate_model_a(self.emp, Decimal('0.5'), Decimal('1'))
        self.assertEqual(result['adjusted_base'], Decimal('1200.00'))
        self.assertTrue(result['capped'])
        self.assertFalse(result['floored'])

    def test_hitting_floor(self):
        result = calculate_model_a(self.emp, Decimal('-0.5'), Decimal('1'))
        self.assertEqual(result['adjusted_base'], Decimal('900.00'))
        self.assertFalse(result['capped'])
        self.assertTrue(result['floored'])

    def test_run_model_a_for_all(self):
        emp2 = Employee.objects.create(
            name='Test2',
            base_salary=Decimal('2000.00'),
            pool_share=Decimal('0.0000'),
            target_bonus=Decimal('0.00'),
            performance_score=Decimal('0.0000'),
            last_year_revenue=Decimal('0.00')
        )
        results = run_model_a_for_all(Employee.objects.all(), Decimal('0.1'), Decimal('1'))
        self.assertEqual(len(results), 2)
        names = {r['employee'] for r in results}
        self.assertSetEqual(names, {'Test', 'Test2'})

class ModelBTest(TestCase):
    def setUp(self):
        self.emp = Employee.objects.create(
            name='BTest',
            base_salary=Decimal('1000.00'),
            pool_share=Decimal('0.10'),
            target_bonus=Decimal('500.00'),
            performance_score=Decimal('0.80'),
            last_year_revenue=Decimal('2000.00')
        )
        self.emp2 = Employee.objects.create(
            name='BTest2',
            base_salary=Decimal('1000.00'),
            pool_share=Decimal('0.05'),
            target_bonus=Decimal('300.00'),
            performance_score=Decimal('1.20'),
            last_year_revenue=Decimal('1000.00')
        )

    def test_pool_method(self):
        res = calculate_model_b_pool(self.emp, Decimal('0.10'))  # +10% revenue
        expected_rev = Decimal('2000.00') * Decimal('1.10')
        expected_bonus = Decimal('0.10') * expected_rev
        self.assertEqual(res['current_revenue'], expected_rev.quantize(Decimal('0.01')))
        self.assertEqual(res['bonus'], expected_bonus.quantize(Decimal('0.01')))

    def test_target_method(self):
        res = calculate_model_b_target(self.emp)
        expected_bonus = self.emp.target_bonus * self.emp.performance_score
        self.assertEqual(res['performance_score_used'], Decimal('0.8000'))
        self.assertEqual(res['bonus'], expected_bonus.quantize(Decimal('0.01')))

    def test_run_model_b_for_all(self):
        pool_results = run_model_b_for_all(Employee.objects.all(), Decimal('0'), True)
        target_results = run_model_b_for_all(Employee.objects.all(), Decimal('0'), False)
        self.assertEqual(len(pool_results), 2)
        self.assertEqual(len(target_results), 2)

    def test_run_comparison(self):
        output = run_comparison(Employee.objects.all(), Decimal('0'), Decimal('1'), False)
        self.assertIn('results', output)
        self.assertIn('summary', output)
        self.assertIsInstance(output['results'], list)
        self.assertIn('total_model_a', output['summary'])
        self.assertIn('total_model_b', output['summary'])
        self.assertEqual(len(output['results']), 2)
        names = {r['employee'] for r in output['results']}
        self.assertSetEqual(names, {self.emp.name, self.emp2.name})

class APITest(APITestCase):
    """Test API filtering and sparse field selection functionality."""
    
    def setUp(self):
        """Set up test data for API tests."""
        self.client = APIClient()
        # Use direct URL path
        self.api_url = '/api/employees/'
         
        # Create test employees with different roles
        self.analyst = Employee.objects.create(
            name='John Analyst',
            employee_id='A001',
            base_salary=Decimal('80000.00'),
            pool_share=Decimal('0.05'),
            target_bonus=Decimal('10000.00'),
            performance_score=Decimal('0.85'),
            last_year_revenue=Decimal('500000.00'),
            role='Analyst',
            level=1
        )
         
        self.manager = Employee.objects.create(
            name='Jane Manager',
            employee_id='M001',
            base_salary=Decimal('120000.00'),
            pool_share=Decimal('0.10'),
            target_bonus=Decimal('30000.00'),
            performance_score=Decimal('0.90'),
            last_year_revenue=Decimal('1000000.00'),
            role='Manager',
            level=3
        )
     
    def test_api_list(self):
        """Basic test to verify the API endpoint is working."""
        response = self.client.get(self.api_url)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.data), 2)  # We created 2 employees

class SimulateAPITest(APITestCase):
    """Test the stateless simulation API endpoint."""
    
    def setUp(self):
        """Set up test data for API tests."""
        self.client = APIClient()
        self.simulate_url = '/api/simulate/'
        
        # Sample employee data for simulation
        self.employee_data = [
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
        ]
        
        # Sample configuration for simulation
        self.config_data = {
            "revenue_delta": "0.05",
            "adjustment_factor": "1.0",
            "use_pool_method": False,
            "use_proposed_model": True,
            "current_year": 2025,
            "performance_rating": "Meets Expectations",
            "is_mrt": False,
            "use_overrides": True
        }
    
    def test_simulate_proposed_model(self):
        """Test the simulate endpoint with the proposed model."""
        data = {
            "employees": self.employee_data,
            "config": self.config_data
        }
        
        response = self.client.post(self.simulate_url, data, format='json')
        if response.status_code != 200:
            print(f"Error response: {response.data}")
            
        self.assertEqual(response.status_code, 200)
        
        # Check that we have results and summary in the response
        self.assertIn('results', response.data)
        self.assertIn('summary', response.data)
        
        # Check that we have the correct number of employees in the results
        self.assertEqual(len(response.data['results']), 2)
        
        # Check that the employee names are in the results
        employee_names = [emp['employee'] for emp in response.data['results']]
        self.assertIn('John Analyst', employee_names)
        self.assertIn('Jane Manager', employee_names)
    
    def test_simulate_original_model(self):
        """Test the simulate endpoint with the original model."""
        # Update config to use original model
        config_data = self.config_data.copy()
        config_data['use_proposed_model'] = False
        
        data = {
            "employees": self.employee_data,
            "config": config_data
        }
        
        response = self.client.post(self.simulate_url, data, format='json')
        if response.status_code != 200:
            print(f"Error response: {response.data}")
            
        self.assertEqual(response.status_code, 200)
        
        # Check that we have model_a and model_b in the response
        self.assertIn('model_a', response.data)
        self.assertIn('model_b', response.data)
        
        # Check that we have the correct number of employees in each model
        self.assertEqual(len(response.data['model_a']), 2)
        self.assertEqual(len(response.data['model_b']), 2)
        
        # Check that the employee names are in the results
        model_a_names = [emp['employee'] for emp in response.data['model_a']]
        self.assertIn('John Analyst', model_a_names)
        self.assertIn('Jane Manager', model_a_names)
        
        model_b_names = [emp['employee'] for emp in response.data['model_b']]
        self.assertIn('John Analyst', model_b_names)
        self.assertIn('Jane Manager', model_b_names)
