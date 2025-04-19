from decimal import Decimal

# Model A limits
MAX_INCREASE = Decimal('0.2')  # +20%
MAX_DECREASE = Decimal('-0.1')  # -10%


def calculate_model_a(employee, revenue_delta: Decimal, adjustment_factor: Decimal) -> dict:
    """
    Adjust base salary based on revenue_delta and adjustment_factor with caps/floors.
    Returns dict with original_base, adjusted_base, variable_portion, capped, floored.
    """
    original_base: Decimal = employee.base_salary
    # raw new base calculation
    raw_new = original_base * (Decimal('1') + revenue_delta * adjustment_factor)
    cap_limit = original_base * (Decimal('1') + MAX_INCREASE)
    floor_limit = original_base * (Decimal('1') + MAX_DECREASE)

    if raw_new > cap_limit:
        adjusted_base = cap_limit
        capped = True
        floored = False
    elif raw_new < floor_limit:
        adjusted_base = floor_limit
        capped = False
        floored = True
    else:
        adjusted_base = raw_new
        capped = False
        floored = False

    variable_portion = max(adjusted_base - original_base, Decimal('0'))

    return {
        'employee': employee.name,
        'original_base': original_base,
        'adjusted_base': adjusted_base.quantize(Decimal('0.01')),
        'variable_portion': variable_portion.quantize(Decimal('0.01')),
        'capped': capped,
        'floored': floored,
    }


def run_model_a_for_all(employees, revenue_delta: Decimal, adjustment_factor: Decimal) -> list[dict]:
    """Run Model A for a list of employee instances."""
    results = []
    for emp in employees:
        res = calculate_model_a(emp, revenue_delta, adjustment_factor)
        results.append(res)
    return results


def calculate_model_b_pool(employee, revenue_delta: Decimal) -> dict:
    """
    Model B pool share method: bonus = pool_share * adjusted revenue.
    """
    current_revenue = employee.last_year_revenue * (Decimal('1') + revenue_delta)
    bonus = max(employee.pool_share * current_revenue, Decimal('0'))
    return {
        'employee': employee.name,
        'current_revenue': current_revenue.quantize(Decimal('0.01')),
        'bonus': bonus.quantize(Decimal('0.01'))
    }


def calculate_model_b_target(employee) -> dict:
    """
    Model B target bonus method: bonus = target_bonus * performance_score (capped at 1.0).
    """
    score = min(employee.performance_score, Decimal('1'))
    bonus = employee.target_bonus * score
    return {
        'employee': employee.name,
        'performance_score_used': score.quantize(Decimal('0.0001')),
        'bonus': bonus.quantize(Decimal('0.01'))
    }


def run_model_b_for_all(employees, revenue_delta: Decimal, use_pool_method: bool) -> list[dict]:
    """
    Run Model B for a list of employee instances.
    """
    results = []
    for emp in employees:
        if use_pool_method:
            res = calculate_model_b_pool(emp, revenue_delta)
        else:
            res = calculate_model_b_target(emp)
        results.append(res)
    return results


def run_comparison(employees, revenue_delta: Decimal, adjustment_factor: Decimal, use_pool_method: bool) -> dict:
    """
    Run both Model A and Model B and merge results with summary metrics.
    """
    results = []
    total_model_a = Decimal('0')
    total_model_b = Decimal('0')

    for emp in employees:
        a = calculate_model_a(emp, revenue_delta, adjustment_factor)
        if use_pool_method:
            b = calculate_model_b_pool(emp, revenue_delta)
        else:
            b = calculate_model_b_target(emp)
        a_total = a['adjusted_base']
        b_bonus = b['bonus']
        b_total = (emp.base_salary + b_bonus).quantize(Decimal('0.01'))
        diff = (b_total - a_total).quantize(Decimal('0.01'))

        results.append({
            'employee': emp.name,
            'original_base': a['original_base'],
            'adjusted_base': a_total,
            'variable_portion': a['variable_portion'],
            'bonus': b_bonus,
            'model_a_total': a_total,
            'model_b_total': b_total,
            'difference': diff,
        })

        total_model_a += a_total
        total_model_b += b_total

    summary = {
        'total_model_a': total_model_a.quantize(Decimal('0.01')),
        'total_model_b': total_model_b.quantize(Decimal('0.01'))
    }

    return {'results': results, 'summary': summary}
