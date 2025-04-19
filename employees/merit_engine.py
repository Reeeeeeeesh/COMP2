from decimal import Decimal
from django.db.models import Avg
from .models import TeamRevenue, MeritMatrix, RevenueTrendFactor, KpiAchievement

# Constants for regulatory requirements
DEFERRAL_THRESHOLD = Decimal('500000')  # £500k
DEFERRAL_PERCENTAGE = Decimal('0.4')    # 40%
INSTRUMENT_SPLIT = Decimal('0.5')       # 50% cash/stock
RATIO_ALERT_THRESHOLD = Decimal('1')    # 100% variable to fixed ratio


def get_compa_ratio_quartile(compa_ratio):
    """Determine quartile based on compa-ratio"""
    if compa_ratio is None:
        return 'Q2'  # Default to middle quartile if no data
    
    if compa_ratio < Decimal('0.85'):
        return 'Q1'
    elif compa_ratio < Decimal('1.0'):
        return 'Q2'
    elif compa_ratio < Decimal('1.15'):
        return 'Q3'
    else:
        return 'Q4'


def get_team_revenue_trend(team, current_year):
    """
    Calculate 3-year revenue trend for a team
    Returns trend category: 'Strong Growth', 'Stable', or 'Decline'
    """
    if team is None:
        return 'Stable'  # Default if no team assigned
    
    # Get last 3 years of revenue data
    revenues = TeamRevenue.objects.filter(
        team=team,
        year__gte=current_year-3,
        year__lt=current_year
    ).order_by('year')
    
    if revenues.count() < 2:
        return 'Stable'  # Not enough data
    
    # Calculate average year-over-year growth
    prev_revenue = None
    growth_rates = []
    
    for rev in revenues:
        if prev_revenue:
            growth = (rev.revenue - prev_revenue) / prev_revenue
            growth_rates.append(growth)
        prev_revenue = rev.revenue
    
    avg_growth = sum(growth_rates) / len(growth_rates)
    
    # Categorize trend
    if avg_growth > Decimal('0.05'):  # >5% growth
        return 'Strong Growth'
    elif avg_growth > Decimal('-0.03'):  # Between -3% and 5%
        return 'Stable'
    else:  # <-3% growth
        return 'Decline'


def get_trend_factor(trend_category):
    """Get revenue trend adjustment factor from database"""
    try:
        factor = RevenueTrendFactor.objects.get(trend_category=trend_category)
        return factor.adjustment_factor
    except RevenueTrendFactor.DoesNotExist:
        # Default factors if not in database
        if trend_category == 'Strong Growth':
            return Decimal('1.25')
        elif trend_category == 'Stable':
            return Decimal('1.0')
        else:  # Decline
            return Decimal('0.75')


def get_merit_increase(performance_rating, compa_ratio_quartile):
    """Get merit increase percentage from merit matrix"""
    try:
        matrix_entry = MeritMatrix.objects.get(
            performance_rating=performance_rating,
            compa_ratio_range=compa_ratio_quartile
        )
        return matrix_entry.increase_percentage
    except MeritMatrix.DoesNotExist:
        # Default values if not in database
        # These are illustrative and should be replaced with actual matrix values
        default_matrix = {
            'Exceeds Expectations': {'Q1': Decimal('0.05'), 'Q2': Decimal('0.04'), 
                                    'Q3': Decimal('0.03'), 'Q4': Decimal('0.02')},
            'Meets Expectations': {'Q1': Decimal('0.03'), 'Q2': Decimal('0.02'), 
                                  'Q3': Decimal('0.01'), 'Q4': Decimal('0.005')},
            'Below Expectations': {'Q1': Decimal('0.01'), 'Q2': Decimal('0.005'), 
                                  'Q3': Decimal('0'), 'Q4': Decimal('0')}
        }
        
        # Default to Meets Expectations, Q2 if rating not found
        rating = performance_rating if performance_rating in default_matrix else 'Meets Expectations'
        quartile = compa_ratio_quartile if compa_ratio_quartile in default_matrix[rating] else 'Q2'
        
        return default_matrix[rating][quartile]


def calculate_merit_increase(employee, current_year=2025):
    """
    Calculate merit increase based on performance rating, compa-ratio, and team revenue trend
    """
    # Get compa-ratio quartile
    compa_ratio = employee.compa_ratio
    quartile = get_compa_ratio_quartile(compa_ratio)
    
    # Get performance rating (default if not set)
    performance_rating = employee.performance_rating or 'Meets Expectations'
    
    # Get team revenue trend
    trend_category = get_team_revenue_trend(employee.team, current_year)
    trend_factor = get_trend_factor(trend_category)
    
    # Get base merit increase from matrix
    base_merit = get_merit_increase(performance_rating, quartile)
    
    # Apply trend factor
    adjusted_merit = base_merit * trend_factor
    
    # Calculate new salary
    original_salary = employee.base_salary
    new_salary = original_salary * (Decimal('1') + adjusted_merit)
    
    return {
        'employee': employee.name,
        'original_salary': original_salary,
        'compa_ratio': compa_ratio,
        'compa_ratio_quartile': quartile,
        'performance_rating': performance_rating,
        'team_revenue_trend': trend_category,
        'base_merit_increase': base_merit,
        'trend_factor': trend_factor,
        'adjusted_merit_increase': adjusted_merit,
        'new_salary': new_salary.quantize(Decimal('0.01')),
        'increase_amount': (new_salary - original_salary).quantize(Decimal('0.01')),
    }


def calculate_bonus(employee, current_year=2025):
    """
    Calculate bonus based on KPI achievement
    """
    try:
        kpi = KpiAchievement.objects.get(employee=employee, year=current_year)
    except KpiAchievement.DoesNotExist:
        # Default to using performance_score if no KPI data
        achievement = employee.performance_score
        return {
            'employee': employee.name,
            'kpi_achievement': achievement,
            'target_bonus': employee.target_bonus,
            'bonus_amount': (employee.target_bonus * achievement).quantize(Decimal('0.01')),
        }
    
    # Calculate weighted KPI achievement
    # These weights should be configurable in a real system
    weights = {
        'investment_performance': Decimal('0.4'),  # 40%
        'risk_management': Decimal('0.2'),         # 20%
        'aum_revenue': Decimal('0.3'),             # 30%
        'qualitative': Decimal('0.1')              # 10%
    }
    
    weighted_achievement = (
        kpi.investment_performance * weights['investment_performance'] +
        kpi.risk_management * weights['risk_management'] +
        kpi.aum_revenue * weights['aum_revenue'] +
        kpi.qualitative * weights['qualitative']
    )
    
    bonus_amount = employee.target_bonus * weighted_achievement
    
    return {
        'employee': employee.name,
        'investment_performance': kpi.investment_performance,
        'risk_management': kpi.risk_management,
        'aum_revenue': kpi.aum_revenue,
        'qualitative': kpi.qualitative,
        'weighted_achievement': weighted_achievement,
        'target_bonus': employee.target_bonus,
        'bonus_amount': bonus_amount.quantize(Decimal('0.01')),
    }


def apply_regulatory_requirements(bonus_amount, is_mrt):
    """Apply regulatory requirements to bonus amount"""
    if not is_mrt:
        return {
            'immediate_cash': bonus_amount,
            'deferred_amount': Decimal('0'),
            'deferred_cash': Decimal('0'),
            'deferred_instruments': Decimal('0'),
            'deferral_applied': False,
            'ratio_alert': False
        }
    
    # Check if deferral applies
    if bonus_amount > DEFERRAL_THRESHOLD:
        deferred_amount = bonus_amount * DEFERRAL_PERCENTAGE
        immediate_amount = bonus_amount - deferred_amount
        
        # Split deferred amount between cash and instruments
        deferred_cash = deferred_amount * (Decimal('1') - INSTRUMENT_SPLIT)
        deferred_instruments = deferred_amount * INSTRUMENT_SPLIT
    else:
        immediate_amount = bonus_amount
        deferred_amount = Decimal('0')
        deferred_cash = Decimal('0')
        deferred_instruments = Decimal('0')
    
    return {
        'immediate_cash': immediate_amount.quantize(Decimal('0.01')),
        'deferred_amount': deferred_amount.quantize(Decimal('0.01')),
        'deferred_cash': deferred_cash.quantize(Decimal('0.01')),
        'deferred_instruments': deferred_instruments.quantize(Decimal('0.01')),
        'deferral_applied': deferred_amount > 0,
        'ratio_alert': (bonus_amount / employee.base_salary) > RATIO_ALERT_THRESHOLD if employee.base_salary else False
    }


def run_proposed_model(employee, current_year=2025):
    """
    Run the proposed compensation model for an employee
    """
    # Calculate merit increase
    merit_result = calculate_merit_increase(employee, current_year)
    
    # Calculate bonus
    bonus_result = calculate_bonus(employee, current_year)
    
    # Apply regulatory requirements
    reg_result = apply_regulatory_requirements(
        bonus_result['bonus_amount'], 
        employee.is_mrt
    )
    
    # Combine results
    total_comp = merit_result['new_salary'] + bonus_result['bonus_amount']
    
    return {
        'employee': employee.name,
        'original_salary': merit_result['original_salary'],
        'new_salary': merit_result['new_salary'],
        'salary_increase': merit_result['increase_amount'],
        'performance_rating': merit_result['performance_rating'],
        'compa_ratio': merit_result['compa_ratio'],
        'team_revenue_trend': merit_result['team_revenue_trend'],
        'bonus_amount': bonus_result['bonus_amount'],
        'total_compensation': total_comp.quantize(Decimal('0.01')),
        'immediate_cash': reg_result['immediate_cash'],
        'deferred_amount': reg_result['deferred_amount'],
        'deferred_cash': reg_result['deferred_cash'],
        'deferred_instruments': reg_result['deferred_instruments'],
        'deferral_applied': reg_result['deferral_applied'],
        'ratio_alert': reg_result['ratio_alert']
    }


def run_proposed_model_for_all(employees, current_year=2025):
    """Run proposed model for multiple employees"""
    results = []
    total_comp = Decimal('0')
    
    for emp in employees:
        result = run_proposed_model(emp, current_year)
        results.append(result)
        total_comp += result['total_compensation']
    
    summary = {
        'total_compensation': total_comp.quantize(Decimal('0.01')),
        'employee_count': len(results)
    }
    
    return {'results': results, 'summary': summary}
