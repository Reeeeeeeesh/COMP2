# DRF ping endpoint
from rest_framework.decorators import api_view
from rest_framework.response import Response
from decimal import Decimal
import csv
from .models import Employee
from .serializers import EmployeeSerializer
from .compensation_engine import run_comparison
from .merit_engine import run_proposed_model_for_all
from rest_framework import status

@api_view(['GET'])
def ping(request):
    return Response({'message': 'pong'})

# Create your views here.

@api_view(['POST'])
def upload_data(request):
    file = request.FILES.get('file')
    if not file:
        return Response({'error': 'No file provided'}, status=400)
    try:
        decoded = file.read().decode('utf-8').splitlines()
    except Exception as e:
        return Response({'error': f'Error reading file: {str(e)}'}, status=400)
    reader = csv.DictReader(decoded)
    required = ['name', 'base_salary', 'pool_share', 'target_bonus', 'performance_score', 'last_year_revenue']
    if not set(required).issubset(set(reader.fieldnames or [])):
        return Response({'error': 'Missing required columns', 'found': reader.fieldnames}, status=400)
    created, updated, errors = [], [], []
    for idx, row in enumerate(reader, start=2):
        try:
            data = {
                'base_salary': Decimal(row['base_salary']),
                'pool_share': Decimal(row['pool_share']),
                'target_bonus': Decimal(row['target_bonus']),
                'performance_score': Decimal(row['performance_score']),
                'last_year_revenue': Decimal(row['last_year_revenue']),
            }
            emp, created_flag = Employee.objects.update_or_create(name=row['name'], defaults=data)
            if created_flag:
                created.append(emp.name)
            else:
                updated.append(emp.name)
        except Exception as e:
            errors.append({'row': idx, 'error': str(e)})
    return Response({'created': created, 'updated': updated, 'errors': errors})

@api_view(['GET', 'POST'])
def employees_list(request):
    """List all employees or create a new one."""
    if request.method == 'GET':
        queryset = Employee.objects.all()
        serializer = EmployeeSerializer(queryset, many=True)
        return Response(serializer.data)

    # POST
    serializer = EmployeeSerializer(data=request.data)
    if serializer.is_valid():
        serializer.save()
        return Response(serializer.data, status=201)
    return Response(serializer.errors, status=400)

@api_view(['POST'])
def calculate(request):
    """Run Model A and B comparison for all employees."""
    try:
        # Get common parameters
        revenue_delta = Decimal(str(request.data.get('revenue_delta', 0)))
        
        # Get model-specific parameters
        adjustment_factor = Decimal(str(request.data.get('adjustment_factor', 1)))
        use_pool_method = bool(request.data.get('use_pool_method', False))
        
        # Get model selection parameter
        use_proposed_model = bool(request.data.get('use_proposed_model', False))
        current_year = int(request.data.get('current_year', 2025))
    except Exception as e:
        return Response({'error': f'Invalid parameters: {str(e)}'}, status=status.HTTP_400_BAD_REQUEST)
    
    employees = Employee.objects.all()
    
    # Run selected model
    if use_proposed_model:
        output = run_proposed_model_for_all(employees, current_year)
    else:
        output = run_comparison(employees, revenue_delta, adjustment_factor, use_pool_method)
        
    return Response(output)
