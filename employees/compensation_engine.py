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
        'team': getattr(employee.team, 'name', 'Unassigned'),  # Safely get team name
        'original_base': float(original_base.quantize(Decimal('0.01'))),
        'adjusted_base': float(adjusted_base.quantize(Decimal('0.01'))),
        'variable_portion': float(variable_portion.quantize(Decimal('0.01'))),
        'capped': capped,
        'floored': floored,
    }


def calculate_model_a_for_all(employees, revenue_delta: Decimal, adjustment_factor: Decimal) -> dict:
    """
    Run model A for all employees and return results with summary
    """
    results = []
    total_comp = Decimal('0')
    team_data = {}

    for employee in employees:
        result = calculate_model_a(employee, revenue_delta, adjustment_factor)
        results.append(result)
        total_comp += Decimal(str(result['adjusted_base']))

        # Process team data
        team = result['team']
        if team not in team_data:
            team_data[team] = {
                'name': team,
                'employee_count': 0,
                'base_salary': Decimal('0'),
                'bonus': Decimal('0'),
                'total': Decimal('0')
            }
        
        team_data[team]['employee_count'] += 1
        team_data[team]['base_salary'] += Decimal(str(result['original_base']))
        team_data[team]['bonus'] += Decimal(str(result['variable_portion']))
        team_data[team]['total'] += Decimal(str(result['adjusted_base']))

    # Convert team data to list and calculate percentages
    team_breakdown = []
    for team in team_data.values():
        team_breakdown.append({
            'name': team['name'],
            'employee_count': team['employee_count'],
            'base_salary': float(team['base_salary'].quantize(Decimal('0.01'))),
            'bonus': float(team['bonus'].quantize(Decimal('0.01'))),
            'total': float(team['total'].quantize(Decimal('0.01'))),
            'salary_percentage': float((team['base_salary'] / team['total'] * 100).quantize(Decimal('0.1'))),
            'bonus_percentage': float((team['bonus'] / team['total'] * 100).quantize(Decimal('0.1')))
        })

    # Sort by total compensation
    team_breakdown.sort(key=lambda x: x['total'], reverse=True)

    summary = {
        'total_compensation': float(total_comp.quantize(Decimal('0.01'))),
        'employee_count': len(results),
        'team_breakdown': team_breakdown
    }

    return {'results': results, 'summary': summary}


def calculate_model_b_pool(employee, revenue_delta: Decimal) -> dict:
    """
    Model B pool share method: bonus = pool_share * adjusted revenue.
    """
    current_revenue = employee.last_year_revenue * (Decimal('1') + revenue_delta)
    bonus = max(employee.pool_share * current_revenue, Decimal('0'))
    return {
        'employee': employee.name,
        'current_revenue': float(current_revenue.quantize(Decimal('0.01'))),
        'bonus': float(bonus.quantize(Decimal('0.01')))
    }


def calculate_model_b_target(employee) -> dict:
    """
    Model B target bonus method: bonus = target_bonus * performance_score (capped at 1.0).
    """
    score = min(employee.performance_score, Decimal('1'))
    bonus = employee.target_bonus * score
    return {
        'employee': employee.name,
        'performance_score_used': float(score.quantize(Decimal('0.0001'))),
        'bonus': float(bonus.quantize(Decimal('0.01')))
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
        a_total = Decimal(str(a['adjusted_base']))
        b_bonus = Decimal(str(b['bonus']))
        b_total = (emp.base_salary + b_bonus).quantize(Decimal('0.01'))
        diff = (b_total - a_total).quantize(Decimal('0.01'))

        results.append({
            'employee': emp.name,
            'original_base': float(a['original_base']),
            'adjusted_base': float(a_total),
            'variable_portion': float(a['variable_portion']),
            'bonus': float(b_bonus),
            'model_a_total': float(a_total),
            'model_b_total': float(b_total),
            'difference': float(diff),
        })

        total_model_a += a_total
        total_model_b += b_total

    summary = {
        'total_model_a': float(total_model_a.quantize(Decimal('0.01'))),
        'total_model_b': float(total_model_b.quantize(Decimal('0.01')))
    }

    return {'results': results, 'summary': summary}


def run_comparison_for_all(employees, revenue_delta: Decimal, adjustment_factor: Decimal, use_pool_method: bool = False) -> dict:
    """
    Run both Model A and Model B and merge results with summary metrics.
    """
    results = []
    total_model_a = Decimal('0')
    total_model_b = Decimal('0')
    team_data = {}

    for emp in employees:
        a = calculate_model_a(emp, revenue_delta, adjustment_factor)
        if use_pool_method:
            b = calculate_model_b_pool(emp, revenue_delta)
        else:
            b = calculate_model_b_target(emp)
        a_total = Decimal(str(a['adjusted_base']))
        b_bonus = Decimal(str(b['bonus']))
        b_total = (emp.base_salary + b_bonus).quantize(Decimal('0.01'))
        diff = (b_total - a_total).quantize(Decimal('0.01'))

        results.append({
            'employee': emp.name,
            'team': a['team'],  # Use team from model A calculation
            'original_base': float(a['original_base']),
            'adjusted_base': float(a_total),
            'variable_portion': float(a['variable_portion']),
            'bonus': float(b_bonus),
            'model_a_total': float(a_total),
            'model_b_total': float(b_total),
            'difference': float(diff),
        })

        # Process team data
        team = a['team']
        if team not in team_data:
            team_data[team] = {
                'name': team,
                'employee_count': 0,
                'base_salary': Decimal('0'),
                'bonus': Decimal('0'),
                'total': Decimal('0')
            }
        
        team_data[team]['employee_count'] += 1
        team_data[team]['base_salary'] += Decimal(str(a['original_base']))
        team_data[team]['bonus'] += Decimal(str(a['variable_portion']))
        team_data[team]['total'] += Decimal(str(a_total))

        total_model_a += a_total
        total_model_b += b_total

    # Convert team data to list and calculate percentages
    team_breakdown = []
    for team in team_data.values():
        team_breakdown.append({
            'name': team['name'],
            'employee_count': team['employee_count'],
            'base_salary': float(team['base_salary'].quantize(Decimal('0.01'))),
            'bonus': float(team['bonus'].quantize(Decimal('0.01'))),
            'total': float(team['total'].quantize(Decimal('0.01'))),
            'salary_percentage': float((team['base_salary'] / team['total'] * 100).quantize(Decimal('0.1'))),
            'bonus_percentage': float((team['bonus'] / team['total'] * 100).quantize(Decimal('0.1')))
        })

    # Sort by total compensation
    team_breakdown.sort(key=lambda x: x['total'], reverse=True)

    summary = {
        'total_model_a': float(total_model_a.quantize(Decimal('0.01'))),
        'total_model_b': float(total_model_b.quantize(Decimal('0.01'))),
        'team_breakdown': team_breakdown,
        'employee_count': len(results)
    }

    return {'results': results, 'summary': summary}
