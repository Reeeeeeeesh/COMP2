from decimal import Decimal
from django.test import TestCase
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
