# DRF ping endpoint
from rest_framework.decorators import api_view
from rest_framework.response import Response
from decimal import Decimal, InvalidOperation
import csv
from .models import Employee, SalaryBand, TeamRevenue, MeritMatrix, RevenueTrendFactor, KpiAchievement, Team, CompensationConfig, DataSnapshot, EmployeeSnapshot, ConfigSnapshot, Scenario, ScenarioEmployeeOverride, ScenarioVersion, ScenarioComparison, ComparisonItem
from .serializers import (
    EmployeeSerializer, SalaryBandSerializer, TeamRevenueSerializer, MeritMatrixSerializer, 
    RevenueTrendFactorSerializer, KpiAchievementSerializer, CompensationConfigSerializer,
    DataSnapshotSerializer, DataSnapshotCreateSerializer, TeamSerializer,
    ScenarioSerializer, ScenarioEmployeeOverrideSerializer, ScenarioVersionSerializer, ScenarioComparisonSerializer, ComparisonItemSerializer
)
from .compensation_engine import run_comparison
from .merit_engine import run_proposed_model_for_all
from rest_framework import status, viewsets, filters
from rest_framework.views import APIView
from rest_framework.parsers import MultiPartParser
from django.db import transaction
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework import filters
from rest_framework.decorators import action
import logging
logger = logging.getLogger(__name__)

class DynamicFieldsViewSetMixin:
    """
    Mixin for ViewSets that support dynamic field selection.
    """
    def get_serializer(self, *args, **kwargs):
        # Get fields from query params for DynamicFieldsMixin
        fields = self.request.query_params.get('fields', None)
        if fields:
            kwargs['fields'] = fields
        return super().get_serializer(*args, **kwargs)

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
    
    # Debug: Print CSV headers
    print("CSV HEADERS:", reader.fieldnames)
    
    required = ['name', 'base_salary', 'pool_share', 'target_bonus', 'performance_score', 'last_year_revenue']
    if not set(required).issubset(set(reader.fieldnames or [])):
        return Response({'error': 'Missing required columns', 'found': reader.fieldnames}, status=400)
    created, updated, errors = [], [], []
    for idx, row in enumerate(reader, start=2):
        # Debug: Print each row
        print(f"ROW {idx}: {row}")
        
        try:
            data = {
                'base_salary': Decimal(row['base_salary']),
                'pool_share': Decimal(row['pool_share']),
                'target_bonus': Decimal(row['target_bonus']),
                'performance_score': Decimal(row['performance_score']),
                'last_year_revenue': Decimal(row['last_year_revenue']),
                # Add additional fields if present in the CSV
                'role': row.get('role', None),
                'level': row.get('level', None),
                'is_mrt': row.get('is_mrt', '').lower() == 'true',
                'performance_rating': row.get('performance_rating', '').strip() or None, # Strip whitespace, store None if empty
            }
            
            # Handle team association by team_name
            if 'team_name' in row and row['team_name'].strip():
                try:
                    team = Team.objects.filter(name=row['team_name']).first()
                    if team:
                        data['team'] = team
                    else:
                        print(f"WARNING: Team '{row['team_name']}' not found for employee '{row['name']}'")
                except Exception as e:
                    print(f"ERROR finding team by name: {str(e)}")
            
            # Handle team association by team ID (this takes precedence if both are provided)
            elif 'team' in row and row['team'].strip():
                try:
                    team_id = int(row['team'])
                    team = Team.objects.filter(id=team_id).first()
                    if team:
                        data['team'] = team
                    else:
                        print(f"WARNING: Team with ID {team_id} not found for employee '{row['name']}'")
                except ValueError:
                    print(f"WARNING: Invalid team ID '{row['team']}' for employee '{row['name']}'")
                except Exception as e:
                    print(f"ERROR finding team by ID: {str(e)}")
            
            # Handle employee_id if present
            if 'employee_id' in row and row['employee_id'].strip():
                try:
                    # Ensure employee_id is stored as an integer
                    data['employee_id'] = int(row['employee_id'])
                    print(f"Setting employee_id to {data['employee_id']} for {row['name']}")
                    
                    # Use employee_id for lookup if available
                    emp, created_flag = Employee.objects.update_or_create(
                        employee_id=data['employee_id'], 
                        defaults={**data, 'name': row['name']}
                    )
                except ValueError:
                    print(f"ERROR: Invalid employee_id format: {row['employee_id']}")
                    return Response({'error': f'Invalid employee_id in row {idx}: {row["employee_id"]}'}, status=400)
            else:
                # Fall back to using name for lookup
                emp, created_flag = Employee.objects.update_or_create(name=row['name'], defaults=data)
            
            # Debug: Print processed data
            print(f"PROCESSED DATA: {data}")
            
            # Debug: Print employee after save
            print(f"SAVED EMPLOYEE: {emp.name}, ID: {emp.employee_id}, Rating: {emp.performance_rating}, MRT: {emp.is_mrt}")
            
            if created_flag:
                created.append(emp.name)
            else:
                updated.append(emp.name)
        except Exception as e:
            print(f"ERROR processing row {idx}: {str(e)}")
            errors.append({'row': idx, 'error': str(e)})
    return Response({'created': created, 'updated': updated, 'errors': errors})

@api_view(['POST', 'OPTIONS'])
def debug_upload(request):
    """Debug endpoint for employee CSV upload"""
    try:
        print("Debug upload endpoint called")
        
        if request.method == 'OPTIONS':
            return Response(status=status.HTTP_200_OK)
            
        if 'file' not in request.FILES:
            print("No file in request")
            return Response({'error': 'No file provided'}, status=status.HTTP_400_BAD_REQUEST)
            
        file = request.FILES['file']
        print(f"Received file: {file.name}, size: {file.size} bytes")
        
        # Check file extension
        if not file.name.endswith('.csv'):
            print("File is not a CSV")
            return Response({'error': 'File must be a CSV'}, status=status.HTTP_400_BAD_REQUEST)
            
        # Process the file
        created = []
        updated = []
        errors = []
        
        try:
            # Decode the file
            file_data = file.read().decode('utf-8-sig')
            csv_data = csv.reader(StringIO(file_data), delimiter=',')
            
            # Get headers
            headers = next(csv_data)
            print(f"CSV Headers: {headers}")
            
            # Check required columns
            required_columns = ['name', 'base_salary', 'pool_share', 'target_bonus', 
                               'performance_score', 'last_year_revenue']
            missing_columns = [col for col in required_columns if col not in headers]
            
            if missing_columns:
                print(f"Missing required columns: {missing_columns}")
                return Response({
                    'error': f'Missing required columns: {", ".join(missing_columns)}'
                }, status=status.HTTP_400_BAD_REQUEST)
                
            # Process rows
            for i, row in enumerate(csv_data, start=1):
                if not any(row):  # Skip empty rows
                    continue
                    
                # Convert row to dict
                row_dict = {headers[i]: val for i, val in enumerate(row) if i < len(headers)}
                print(f"Processing row {i}: {row_dict}")
                
                try:
                    # Check if employee exists
                    employee_id = row_dict.get('employee_id')
                    name = row_dict.get('name')
                    
                    if employee_id:
                        # Try to find by employee_id first
                        employees = Employee.objects.filter(employee_id=employee_id)
                        if employees.exists():
                            employee = employees.first()
                            action = 'updated'
                        else:
                            employee = None
                            action = 'created'
                    elif name:
                        # Try to find by name
                        employees = Employee.objects.filter(name=name)
                        if employees.exists():
                            employee = employees.first()
                            action = 'updated'
                        else:
                            employee = None
                            action = 'created'
                    else:
                        errors.append({
                            'row': i,
                            'error': 'Employee must have either employee_id or name'
                        })
                        continue
                        
                    # Create or update employee
                    if not employee:
                        employee = Employee()
                        
                    # Update fields
                    for field in ['employee_id', 'name', 'base_salary', 'pool_share', 
                                 'target_bonus', 'performance_score', 'last_year_revenue',
                                 'role', 'level', 'is_mrt', 'performance_rating']:
                        if field in row_dict and row_dict[field]:
                            # Handle boolean field
                            if field == 'is_mrt':
                                value = row_dict[field].lower() in ['true', 'yes', '1']
                            # Handle numeric fields
                            elif field in ['base_salary', 'pool_share', 'target_bonus', 
                                         'performance_score', 'last_year_revenue']:
                                try:
                                    value = Decimal(row_dict[field].replace(',', ''))
                                except:
                                    errors.append({
                                        'row': i,
                                        'error': f'Invalid value for {field}: {row_dict[field]}'
                                    })
                                    continue
                            else:
                                value = row_dict[field]
                                
                            setattr(employee, field, value)
                            
                    # Handle team field
                    if 'team' in row_dict and row_dict['team']:
                        team_name = row_dict['team']
                        team, created = Team.objects.get_or_create(name=team_name)
                        employee.team = team
                        
                    # Save employee
                    employee.save()
                    
                    if action == 'created':
                        created.append(employee.name)
                    else:
                        updated.append(employee.name)
                        
                except Exception as e:
                    print(f"Error processing row {i}: {str(e)}")
                    errors.append({
                        'row': i,
                        'error': str(e)
                    })
                    
            return Response({
                'created': created,
                'updated': updated,
                'errors': errors
            })
            
        except UnicodeDecodeError:
            print("Unicode decode error")
            return Response({
                'error': 'File encoding not supported. Please use UTF-8.'
            }, status=status.HTTP_400_BAD_REQUEST)
            
    except Exception as e:
        print(f"Unexpected error: {str(e)}")
        return Response({'error': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

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
    print("REQUEST DATA:", request.data)
    try:
        # Get common parameters
        revenue_delta = Decimal(str(request.data.get('revenue_delta', 0)))
        
        # Get model-specific parameters
        adjustment_factor = Decimal(str(request.data.get('adjustment_factor', 1)))
        use_pool_method = bool(request.data.get('use_pool_method', False))
        
        # Get model selection parameter
        use_proposed_model = bool(request.data.get('use_proposed_model', False))
        current_year = int(request.data.get('current_year', 2025))
        # Get proposed model parameters
        performance_rating = request.data.get('performance_rating', 'Meets Expectations')
        is_mrt = bool(request.data.get('is_mrt', False))
        use_overrides = bool(request.data.get('use_overrides', True))
        
        print("PARAMS:", {
            "use_proposed_model": use_proposed_model,
            "performance_rating": performance_rating,
            "is_mrt": is_mrt,
            "use_overrides": use_overrides,
            "current_year": current_year
        })
    except Exception as e:
        print("ERROR:", str(e))
        return Response({'error': f'Invalid parameters: {str(e)}'}, status=status.HTTP_400_BAD_REQUEST)
    
    # If using proposed model without overrides, calculate only on employees imported via CSV (have a performance_rating)
    if use_proposed_model and not use_overrides:
        employees = Employee.objects.filter(performance_rating__isnull=False).exclude(performance_rating='')
    else:
        employees = Employee.objects.all()
    print("EMPLOYEE COUNT:", employees.count())
    for emp in employees[:3]:  # Print first 3 for debugging
        print(f"EMPLOYEE: {emp.name}, Rating: {emp.performance_rating}, MRT: {emp.is_mrt}")
    
    # Run selected model
    if use_proposed_model:
        if use_overrides:
            output = run_proposed_model_for_all(employees, current_year, performance_rating, is_mrt)
        else:
            output = run_proposed_model_for_all(employees, current_year)
    else:
        output = run_comparison(employees, revenue_delta, adjustment_factor, use_pool_method)
        
    return Response(output)

@api_view(['POST'])
def simulate(request):
    """
    Stateless simulation endpoint that calculates compensation without modifying the database.
    
    This endpoint accepts employee data and configuration parameters in the request body
    and returns the calculated compensation without saving anything to the database.
    
    Request format:
    {
        "employees": [
            {
                "name": "John Doe",
                "employee_id": "E001",
                "base_salary": 100000,
                "pool_share": 0.05,
                "target_bonus": 10000,
                "performance_score": 0.9,
                "last_year_revenue": 500000,
                "role": "Analyst",
                "level": 1,
                "team": "Investment",
                "performance_rating": "Exceeds Expectations",
                "is_mrt": false
            },
            ...
        ],
        "config": {
            "revenue_delta": 0.05,
            "adjustment_factor": 1.0,
            "use_pool_method": false,
            "use_proposed_model": true,
            "current_year": 2025,
            "performance_rating": "Meets Expectations",
            "is_mrt": false,
            "use_overrides": true
        }
    }
    """
    from django.db import transaction
    from .merit_engine import run_proposed_model_for_all
    from .compensation_engine import run_comparison
    from .models import Employee, Team
    from decimal import Decimal, InvalidOperation
    
    print("SIMULATE REQUEST DATA:", request.data)
    try:
        # Extract employee data and config from request
        # Handle both formats: direct parameters or nested under 'config'/'employees'
        if 'employees' in request.data and isinstance(request.data['employees'], list):
            employee_data = request.data['employees']
            # Config might be nested or at the top level
            if 'config' in request.data and isinstance(request.data['config'], dict):
                config = request.data['config']
            else:
                # Extract config parameters from top level
                config = {
                    'revenue_delta': request.data.get('revenue_delta', 0),
                    'adjustment_factor': request.data.get('adjustment_factor', 1),
                    'use_pool_method': request.data.get('use_pool_method', False),
                    'use_proposed_model': request.data.get('use_proposed_model', True),
                    'current_year': request.data.get('current_year', 2025),
                    'performance_rating': request.data.get('performance_rating', 'Meets Expectations'),
                    'is_mrt': request.data.get('is_mrt', False),
                    'use_overrides': request.data.get('use_overrides', True)
                }
        else:
            # Assume the request data itself is the employee data (for backward compatibility)
            employee_data = [request.data]
            config = {
                'revenue_delta': 0,
                'adjustment_factor': 1,
                'use_pool_method': False,
                'use_proposed_model': True,
                'current_year': 2025,
                'performance_rating': 'Meets Expectations',
                'is_mrt': False,
                'use_overrides': True
            }
        
        print("EMPLOYEE DATA:", employee_data)
        print("CONFIG:", config)
        
        # Extract config parameters
        try:
            revenue_delta = Decimal(str(config.get('revenue_delta', 0)))
            adjustment_factor = Decimal(str(config.get('adjustment_factor', 1)))
        except (ValueError, TypeError, InvalidOperation) as e:
            print(f"Error converting config values: {e}")
            return Response({
                'error': f'Invalid numeric value in configuration: {e}'
            }, status=status.HTTP_400_BAD_REQUEST)
            
        use_pool_method = bool(config.get('use_pool_method', False))
        use_proposed_model = bool(config.get('use_proposed_model', True))
        current_year = int(config.get('current_year', 2025))
        performance_rating = config.get('performance_rating', 'Meets Expectations')
        is_mrt = bool(config.get('is_mrt', False))
        use_overrides = bool(config.get('use_overrides', True))
        
        # Create temporary employees in a transaction and roll back at the end
        with transaction.atomic():
            # Create temporary Employee objects and save them to the database
            temp_employees = []
            for emp_data in employee_data:
                # Handle numeric values safely
                try:
                    # Convert all numeric values to Decimal with proper precision
                    base_salary = Decimal(str(emp_data.get('base_salary', 0)))
                    pool_share = Decimal(str(emp_data.get('pool_share', 0)))
                    target_bonus = Decimal(str(emp_data.get('target_bonus', 0)))
                    performance_score = Decimal(str(emp_data.get('performance_score', 0)))
                    last_year_revenue = Decimal(str(emp_data.get('last_year_revenue', 0)))
                except (ValueError, TypeError, InvalidOperation) as e:
                    print(f"Error converting numeric values: {e}")
                    return Response({
                        'error': f'Invalid numeric value in employee data: {e}',
                        'employee': emp_data.get('name', 'Unknown')
                    }, status=status.HTTP_400_BAD_REQUEST)
                
                # Handle team relationship
                # Support both 'team' and 'team_name' fields for team
                team_name = emp_data.get('team', emp_data.get('team_name', ''))
                team_obj = None
                if team_name:
                    # Get or create the team (will be rolled back later)
                    team_obj, _ = Team.objects.get_or_create(name=team_name)
                
                # Create Employee instance and save it to the database
                employee = Employee.objects.create(
                    name=emp_data.get('name', ''),
                    employee_id=emp_data.get('employee_id', ''),
                    base_salary=base_salary,
                    pool_share=pool_share,
                    target_bonus=target_bonus,
                    performance_score=performance_score,
                    last_year_revenue=last_year_revenue,
                    role=emp_data.get('role', ''),
                    level=emp_data.get('level', 0),
                    team=team_obj,
                    performance_rating=emp_data.get('performance_rating', ''),
                    is_mrt=emp_data.get('is_mrt', False)
                )
                
                temp_employees.append(employee)
            
            # Run selected model
            if use_proposed_model:
                if use_overrides:
                    output = run_proposed_model_for_all(temp_employees, current_year, performance_rating, is_mrt)
                else:
                    output = run_proposed_model_for_all(temp_employees, current_year)
            else:
                comparison_output = run_comparison(temp_employees, revenue_delta, adjustment_factor, use_pool_method)
                # The test expects model_a and model_b keys
                output = comparison_output
            
            # Roll back the transaction to ensure no data is persisted
            transaction.set_rollback(True)
        
        # Make sure the output format matches what the test expects
        if use_proposed_model and 'results' not in output and isinstance(output, list):
            # If the output is just a list of results, wrap it in the expected format
            total_comp = sum(Decimal(str(result.get('total_compensation', 0))) for result in output)
            output = {
                'results': output,
                'summary': {
                    'total_compensation': total_comp,
                    'employee_count': len(output)
                }
            }
        
        return Response(output)
    except Exception as e:
        import traceback; traceback.print_exc()
        print("SIMULATION ERROR:", str(e))
        return Response({'error': f'Invalid parameters: {str(e)}'}, status=status.HTTP_400_BAD_REQUEST)

# Bulk CSV upload endpoints for configuration models
class SalaryBandUploadView(APIView):
    parser_classes = [MultiPartParser]
    def post(self, request, format=None):
        file = request.FILES.get('file')
        if not file:
            return Response({'detail':'No file provided'}, status=status.HTTP_400_BAD_REQUEST)
        data = file.read().decode('utf-8').splitlines()
        reader = csv.DictReader(data)
        errors = []
        for idx, row in enumerate(reader, start=1):
            serializer = SalaryBandSerializer(data=row)
            if serializer.is_valid(): serializer.save()
            else: errors.append({'row': idx, 'errors': serializer.errors})
        if errors: return Response({'errors': errors}, status=status.HTTP_400_BAD_REQUEST)
        return Response({'detail':'Upload successful'}, status=status.HTTP_201_CREATED)

class TeamRevenueUploadView(APIView):
    parser_classes = [MultiPartParser]
    def post(self, request, format=None):
        file = request.FILES.get('file')
        if not file: return Response({'detail':'No file provided'}, status=status.HTTP_400_BAD_REQUEST)
        data = file.read().decode('utf-8').splitlines()
        reader = csv.DictReader(data)
        errors = []
        for idx, row in enumerate(reader, start=1):
            serializer = TeamRevenueSerializer(data=row)
            if serializer.is_valid(): serializer.save()
            else: errors.append({'row': idx, 'errors': serializer.errors})
        if errors: return Response({'errors': errors}, status=status.HTTP_400_BAD_REQUEST)
        return Response({'detail':'Upload successful'}, status=status.HTTP_201_CREATED)

class MeritMatrixUploadView(APIView):
    parser_classes = [MultiPartParser]
    def post(self, request, format=None):
        file = request.FILES.get('file')
        if not file: return Response({'detail':'No file provided'}, status=status.HTTP_400_BAD_REQUEST)
        data = file.read().decode('utf-8').splitlines()
        reader = csv.DictReader(data)
        errors = []
        for idx, row in enumerate(reader, start=1):
            serializer = MeritMatrixSerializer(data=row)
            if serializer.is_valid(): serializer.save()
            else: errors.append({'row': idx, 'errors': serializer.errors})
        if errors: return Response({'errors': errors}, status=status.HTTP_400_BAD_REQUEST)
        return Response({'detail':'Upload successful'}, status=status.HTTP_201_CREATED)

class RevenueTrendFactorUploadView(APIView):
    parser_classes = [MultiPartParser]
    def post(self, request, format=None):
        file = request.FILES.get('file')
        if not file: return Response({'detail':'No file provided'}, status=status.HTTP_400_BAD_REQUEST)
        data = file.read().decode('utf-8').splitlines()
        reader = csv.DictReader(data)
        errors = []
        for idx, row in enumerate(reader, start=1):
            serializer = RevenueTrendFactorSerializer(data=row)
            if serializer.is_valid(): serializer.save()
            else: errors.append({'row': idx, 'errors': serializer.errors})
        if errors: return Response({'errors': errors}, status=status.HTTP_400_BAD_REQUEST)
        return Response({'detail':'Upload successful'}, status=status.HTTP_201_CREATED)

class KpiAchievementUploadView(APIView):
    parser_classes = [MultiPartParser]
    def post(self, request, format=None):
        file = request.FILES.get('file')
        if not file: return Response({'detail':'No file provided'}, status=status.HTTP_400_BAD_REQUEST)
        data = file.read().decode('utf-8').splitlines()
        reader = csv.DictReader(data)
        errors = []
        for idx, row in enumerate(reader, start=1):
            serializer = KpiAchievementSerializer(data=row)
            if serializer.is_valid(): serializer.save()
            else: errors.append({'row': idx, 'errors': serializer.errors})
        if errors: return Response({'errors': errors}, status=status.HTTP_400_BAD_REQUEST)
        return Response({'detail':'Upload successful'}, status=status.HTTP_201_CREATED)

# Bulk upload all configuration models from a single CSV file
class ConfigBulkUploadView(APIView):
    parser_classes = [MultiPartParser]
    @transaction.atomic
    def post(self, request, format=None):
        file = request.FILES.get('file')
        if not file:
            return Response({'detail':'No file provided'}, status=status.HTTP_400_BAD_REQUEST)
        # Clear previous configuration data so bulk file is the single source of truth
        SalaryBand.objects.all().delete()
        TeamRevenue.objects.all().delete()
        MeritMatrix.objects.all().delete()
        RevenueTrendFactor.objects.all().delete()
        KpiAchievement.objects.all().delete()
        content = file.read().decode('utf-8').replace('\r\n','\n')
        sections = [sec.strip() for sec in content.split('\n\n') if sec.strip()]
        errors = []
        processed = set()
        for sec in sections:
            lines = sec.split('\n')
            raw_header = lines[0].split(',')
            header = [h.strip().lower() for h in raw_header if h.strip()]
            lines[0] = ','.join(header)
            reader = csv.DictReader(lines)
            # Determine model and unique keys by header
            if 'role' in header and 'level' in header:
                model = SalaryBand; unique_keys = ['role','level']
            elif 'team' in header and 'revenue' in header:
                model = TeamRevenue; unique_keys = ['team','year']
            elif 'performance_rating' in header and 'compa_ratio_range' in header:
                model = MeritMatrix; unique_keys = ['performance_rating','compa_ratio_range']
            elif 'trend_category' in header:
                model = RevenueTrendFactor; unique_keys = ['trend_category']
            elif 'investment_performance' in header and 'risk_management' in header:
                model = KpiAchievement; unique_keys = ['employee','year']
            else:
                errors.append({'section': header, 'error': 'Unknown section header'})
                continue
            if model not in processed:
                model.objects.all().delete()
                processed.add(model)
            for idx, row in enumerate(reader, start=1):
                # drop any empty-string keys
                row = {k: v for k, v in row.items() if k}
                # Handle foreign keys and defaults for specific models
                if model is TeamRevenue:
                    team_val = row['team']
                    try:
                        team_obj = Team.objects.get(pk=int(team_val))
                    except (ValueError, Team.DoesNotExist):
                        team_obj, _ = Team.objects.get_or_create(name=team_val)
                    lookup = {'team': team_obj, 'year': int(row['year'])}
                    defaults = {'revenue': Decimal(row['revenue'])}
                # Special handling for KPI Achievements with employee lookup
                elif model is KpiAchievement:
                    # Check for employee_id or employee column
                    emp_id_val = row.get('employee_id', '')
                    if emp_id_val and emp_id_val.strip():
                        try:
                            emp_id_int = int(emp_id_val)
                            # Try to find employee by ID first
                            try:
                                emp_obj = Employee.objects.get(employee_id=emp_id_int)
                                lookup = {'employee': emp_obj, 'year': int(row['year'])}
                            except Employee.DoesNotExist:
                                errors.append({'section': header, 'row': idx, 'errors': f'Employee with ID {emp_id_int} not found'})
                                continue
                        except ValueError:
                            errors.append({'section': header, 'row': idx, 'errors': f'Invalid employee_id: {emp_id_val}'})
                            continue
                    else:
                        emp_name = row.get('employee', '').strip()
                        if not emp_name:
                            errors.append({'section': header, 'row': idx, 'errors': 'Missing employee name or id'})
                            continue
                        try:
                            emp_obj = Employee.objects.get(name=emp_name)
                        except Employee.DoesNotExist:
                            errors.append({'section': header, 'row': idx, 'errors': f'Employee not found: {emp_name}'})
                            continue
                        lookup = {'employee': emp_obj, 'year': int(row['year'])}
                    defaults = {
                        'investment_performance': Decimal(row['investment_performance']),
                        'risk_management': Decimal(row['risk_management']),
                        'aum_revenue': Decimal(row['aum_revenue']),
                        'qualitative': Decimal(row['qualitative']),
                    }
                else:
                    lookup = {k: row[k] for k in unique_keys}
                    defaults = {k: row[k] for k in row if k not in unique_keys}
                try:
                    model.objects.update_or_create(defaults=defaults, **lookup)
                except Exception as e:
                    errors.append({'section': header, 'row': idx, 'errors': str(e)})
        if errors:
            return Response({'errors': errors}, status=status.HTTP_400_BAD_REQUEST)
        return Response({'detail':'All data uploaded successfully'}, status=status.HTTP_201_CREATED)

# Debug endpoint for configuration bulk upload
@api_view(['POST', 'OPTIONS'])
def debug_config_upload(request):
    """Debug endpoint for configuration bulk upload"""
    if request.method == 'OPTIONS':
        return Response({'message': 'CORS preflight successful'})
    
    # Log request details
    print("DEBUG CONFIG UPLOAD - Request received")
    print(f"Content-Type: {request.content_type}")
    
    # Check if file exists
    file = request.FILES.get('file')
    if not file:
        print("DEBUG CONFIG UPLOAD - No file in request")
        return Response({'detail': 'No file provided'}, status=status.HTTP_400_BAD_REQUEST)
    
    # Log file details
    print(f"File name: {file.name}")
    print(f"File size: {file.size}")
    
    try:
        # Try to read the file content
        content = file.read().decode('utf-8')
        print(f"File content sample: {content[:200]}...")
        
        # Reset file pointer
        file.seek(0)
        
        # Check if the file has the expected format (sections separated by blank lines)
        content = file.read().decode('utf-8').replace('\r\n','\n')
        sections = [sec.strip() for sec in content.split('\n\n') if sec.strip()]
        print(f"Found {len(sections)} sections in the file")
        
        if len(sections) == 0:
            return Response({'detail': 'File does not contain any sections. Configuration file should have sections separated by blank lines.'}, status=status.HTTP_400_BAD_REQUEST)
        
        # Analyze each section
        for i, sec in enumerate(sections):
            lines = sec.split('\n')
            if not lines:
                continue
                
            print(f"Section {i+1} header: {lines[0]}")
            
            # Check if the section has a valid header
            raw_header = lines[0].split(',')
            header = [h.strip().lower() for h in raw_header if h.strip()]
            
            # Determine the expected model based on header
            if 'role' in header and 'level' in header:
                print(f"Section {i+1} appears to be Salary Bands")
            elif 'team' in header and 'revenue' in header:
                print(f"Section {i+1} appears to be Team Revenue")
            elif 'performance_rating' in header and 'compa_ratio_range' in header:
                print(f"Section {i+1} appears to be Merit Matrix")
            elif 'trend_category' in header:
                print(f"Section {i+1} appears to be Revenue Trend Factors")
            elif 'investment_performance' in header and 'risk_management' in header:
                print(f"Section {i+1} appears to be KPI Achievements")
            else:
                print(f"Section {i+1} has unknown header: {header}")
        
        # Forward to a modified implementation that handles duplicates
        file.seek(0)
        return safe_config_bulk_upload(request)
        
    except Exception as e:
        print(f"DEBUG CONFIG UPLOAD - Exception: {str(e)}")
        return Response({
            'detail': f'Debug upload error: {str(e)}',
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

# Safe version of ConfigBulkUploadView that handles duplicate employees
@transaction.atomic
def safe_config_bulk_upload(request):
    file = request.FILES.get('file')
    if not file:
        return Response({'detail':'No file provided'}, status=status.HTTP_400_BAD_REQUEST)
    
    # Clear previous configuration data so bulk file is the single source of truth
    SalaryBand.objects.all().delete()
    TeamRevenue.objects.all().delete()
    MeritMatrix.objects.all().delete()
    RevenueTrendFactor.objects.all().delete()
    KpiAchievement.objects.all().delete()
    
    content = file.read().decode('utf-8').replace('\r\n','\n')
    sections = [sec.strip() for sec in content.split('\n\n') if sec.strip()]
    errors = []
    processed = set()
    
    for sec in sections:
        lines = sec.split('\n')
        raw_header = lines[0].split(',')
        header = [h.strip().lower() for h in raw_header if h.strip()]
        lines[0] = ','.join(header)
        reader = csv.DictReader(lines)
        
        # Determine model and unique keys by header
        if 'role' in header and 'level' in header:
            model = SalaryBand; unique_keys = ['role','level']
        elif 'team' in header and 'revenue' in header:
            model = TeamRevenue; unique_keys = ['team','year']
        elif 'performance_rating' in header and 'compa_ratio_range' in header:
            model = MeritMatrix; unique_keys = ['performance_rating','compa_ratio_range']
        elif 'trend_category' in header:
            model = RevenueTrendFactor; unique_keys = ['trend_category']
        elif 'investment_performance' in header and 'risk_management' in header:
            model = KpiAchievement; unique_keys = ['employee','year']
        else:
            errors.append({'section': header, 'error': 'Unknown section header'})
            continue
            
        if model not in processed:
            model.objects.all().delete()
            processed.add(model)
            
        for idx, row in enumerate(reader, start=1):
            # drop any empty-string keys
            row = {k: v for k, v in row.items() if k}
            
            # Handle foreign keys and defaults for specific models
            if model is TeamRevenue:
                team_val = row['team']
                try:
                    team_obj = Team.objects.get(pk=int(team_val))
                except (ValueError, Team.DoesNotExist):
                    team_obj, _ = Team.objects.get_or_create(name=team_val)
                lookup = {'team': team_obj, 'year': int(row['year'])}
                defaults = {'revenue': Decimal(row['revenue'])}
            # Special handling for KPI Achievements with employee lookup
            elif model is KpiAchievement:
                # Check for employee_id or employee column
                emp_id_val = row.get('employee_id', '')
                if emp_id_val and emp_id_val.strip():
                    try:
                        emp_id_int = int(emp_id_val)
                        # Try to find employee by ID first - handle multiple matches
                        employees = Employee.objects.filter(employee_id=emp_id_int)
                        if employees.count() == 0:
                            errors.append({'section': header, 'row': idx, 'errors': f'Employee with ID {emp_id_int} not found'})
                            continue
                        # Use the first employee if multiple matches
                        emp_obj = employees.first()
                        lookup = {'employee': emp_obj, 'year': int(row['year'])}
                    except ValueError:
                        errors.append({'section': header, 'row': idx, 'errors': f'Invalid employee_id: {emp_id_val}'})
                        continue
                else:
                    emp_name = row.get('employee', '').strip()
                    if not emp_name:
                        errors.append({'section': header, 'row': idx, 'errors': 'Missing employee name or id'})
                        continue
                    # Handle multiple employees with the same name
                    employees = Employee.objects.filter(name=emp_name)
                    if employees.count() == 0:
                        errors.append({'section': header, 'row': idx, 'errors': f'Employee not found: {emp_name}'})
                        continue
                    # Use the first employee if multiple matches
                    emp_obj = employees.first()
                    lookup = {'employee': emp_obj, 'year': int(row['year'])}
                defaults = {
                    'investment_performance': Decimal(row['investment_performance']),
                    'risk_management': Decimal(row['risk_management']),
                    'aum_revenue': Decimal(row['aum_revenue']),
                    'qualitative': Decimal(row['qualitative']),
                }
            else:
                lookup = {k: row[k] for k in unique_keys}
                defaults = {k: row[k] for k in row if k not in unique_keys}
            try:
                model.objects.update_or_create(defaults=defaults, **lookup)
            except Exception as e:
                errors.append({'section': header, 'row': idx, 'errors': str(e)})
    
    if errors:
        return Response({'errors': errors}, status=status.HTTP_400_BAD_REQUEST)
    return Response({'detail':'All data uploaded successfully'}, status=status.HTTP_201_CREATED)

# --- REMOVED OLD/DEPRECATED TEAM UPLOAD VIEWS ---
# TeamUploadView, TeamSeedImportView, emergency_team_import, delete_all_teams
# have been removed to avoid confusion. Use definitive_team_upload instead.

# --- The Definitive Team Upload View ---
@api_view(['POST'])
def definitive_team_upload(request):
    """The most robust team CSV upload view possible."""
    logger.info("--- Definitive Team Upload Started ---")
    file = request.FILES.get('file')
    if not file:
        logger.error("Definitive Upload: No file provided.")
        return Response({'detail': 'No file provided'}, status=status.HTTP_400_BAD_REQUEST)

    logger.info(f"Definitive Upload: Received file '{file.name}', size={file.size}, type='{file.content_type}'")

    content = None
    detected_encoding = None
    errors = []

    # 1. Read file content with encoding detection
    try:
        file.seek(0)
        file_bytes = file.read()
        logger.info(f"Definitive Upload: Read {len(file_bytes)} bytes.")
        
        # Try common encodings
        for encoding in ['utf-8-sig', 'utf-8', 'latin-1', 'cp1252']: 
            try:
                content = file_bytes.decode(encoding)
                detected_encoding = encoding
                logger.info(f"Definitive Upload: Successfully decoded using {encoding}.")
                break
            except UnicodeDecodeError:
                logger.warning(f"Definitive Upload: Failed decoding with {encoding}.")
                continue
        
        if content is None:
            errors.append("Could not decode the file using common encodings (utf-8, latin-1, cp1252).")
            logger.error("Definitive Upload: Failed to decode file content with any common encoding.")
            return Response({'detail': 'File encoding not supported or file is corrupt.', 'errors': errors}, status=status.HTTP_400_BAD_REQUEST)
            
    except Exception as e:
        logger.exception("Definitive Upload: Error reading or decoding file.")
        return Response({'detail': f'Error reading file: {str(e)}'}, status=status.HTTP_400_BAD_REQUEST)

    # 2. Process lines
    lines = []
    try:
        # Handle different line endings robustly
        content = content.replace('\r\n', '\n').replace('\r', '\n')
        raw_lines = content.split('\n')
        logger.info(f"Definitive Upload: Split content into {len(raw_lines)} raw lines.")

        # Filter empty lines and skip header
        header_skipped = False
        for i, line_content in enumerate(raw_lines):
            trimmed_line = line_content.strip()
            if not trimmed_line:
                logger.debug(f"Definitive Upload: Skipping empty line {i+1}.")
                continue
            
            if not header_skipped:
                logger.info(f"Definitive Upload: Skipping header line {i+1}: '{trimmed_line[:100]}...' ")
                header_skipped = True
                continue
                
            lines.append({'original_line': i+1, 'content': trimmed_line})
        
        logger.info(f"Definitive Upload: Found {len(lines)} potential data lines after filtering.")
        
        if not lines:
             errors.append("No data lines found after the header (or file only contains a header).")
             logger.error("Definitive Upload: No data lines found after filtering.")
             return Response({'detail': 'No data lines found in the file after the header.', 'errors': errors}, status=status.HTTP_400_BAD_REQUEST)

    except Exception as e:
        logger.exception("Definitive Upload: Error processing lines.")
        return Response({'detail': f'Error processing file lines: {str(e)}'}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    # 3. Extract Team Names (Focus on First Column)
    team_names = []
    line_errors = []
    for line_data in lines:
        line_num = line_data['original_line']
        line_content = line_data['content']
        try:
            # Use csv reader for robust splitting, handling quotes etc.
            reader = csv.reader(io.StringIO(line_content))
            row = next(reader)
            if row:
                team_name = row[0].strip()
                if team_name:
                    if team_name not in team_names:
                         team_names.append(team_name)
                         logger.debug(f"Definitive Upload: Extracted team '{team_name}' from line {line_num}.")
                    else:
                         logger.warning(f"Definitive Upload: Duplicate team name '{team_name}' found on line {line_num}, skipping.")
                else:
                    logger.warning(f"Definitive Upload: Empty team name found in first column on line {line_num}.")
                    line_errors.append(f"Line {line_num}: First column is empty.")
            else:
                 logger.warning(f"Definitive Upload: CSV reader found no columns on line {line_num}.")
                 line_errors.append(f"Line {line_num}: Could not parse any columns.")
        except Exception as parse_error:
            logger.warning(f"Definitive Upload: Error parsing line {line_num} ('{line_content[:50]}...'): {parse_error}")
            line_errors.append(f"Line {line_num}: Error parsing line - {parse_error}")

    logger.info(f"Definitive Upload: Extracted {len(team_names)} unique team names.")

    if not team_names:
        errors.append("Could not extract any valid, unique team names from the first column of the data lines.")
        logger.error("Definitive Upload: Failed to extract any valid team names.")
        return Response({'detail': 'No valid team names found in the file.', 'errors': errors, 'line_errors': line_errors}, status=status.HTTP_400_BAD_REQUEST)

    # 4. Database Operations (Transactional)
    try:
        with transaction.atomic():
            logger.info("Definitive Upload: Starting database transaction.")
            
            # Clear existing teams
            deleted_count, _ = Team.objects.all().delete()
            logger.info(f"Definitive Upload: Deleted {deleted_count} existing teams.")
            
            # Create new teams
            created_teams = []
            for name in team_names:
                team = Team.objects.create(name=name)
                created_teams.append(team.name)
            
            logger.info(f"Definitive Upload: Successfully created {len(created_teams)} new teams.")
            logger.info("--- Definitive Team Upload Successful ---")
            return Response({
                'detail': f'Successfully imported {len(created_teams)} unique teams.',
                'teams_imported': created_teams,
                'line_errors': line_errors # Include any non-fatal line errors
            }, status=status.HTTP_201_CREATED)

    except Exception as e:
        logger.exception("Definitive Upload: Database transaction failed.")
        return Response({'detail': f'Database error during import: {str(e)}'}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

# File inspector endpoint
@api_view(['POST'])
def inspect_csv_file(request):
    """Inspect a CSV file and return its exact content for debugging"""
    logger.info("--- Inspect CSV File Started ---") 
    file = request.FILES.get('file')
    if not file:
        logger.error("Inspect CSV: No file provided.") 
        return Response({'detail':'No file provided'}, status=status.HTTP_400_BAD_REQUEST)
    
    result = {
        'filename': file.name,
        'size_bytes': file.size,
        'content_preview': None,
        'lines': [],
        'encoding_used': None,
        'content_type': file.content_type,
    }
    logger.info(f"Inspect CSV: Analyzing '{file.name}', size={file.size}") 
    
    # Try different encodings
    for encoding in ['utf-8-sig', 'utf-8', 'latin-1', 'ascii', 'cp1252']: 
        try:
            # Reset file position
            file.seek(0)
            content = file.read().decode(encoding)
            result['encoding_used'] = encoding
            logger.info(f"Inspect CSV: Decoded using {encoding}.") 
            
            # Get content preview (first 500 chars)
            result['content_preview'] = content[:500] 
            
            # Get lines
            content_for_lines = content.replace('\r\n', '\n').replace('\r', '\n') 
            lines = content_for_lines.split('\n')
            result['line_count'] = len(lines)
            
            # Store first 50 lines
            for i, line in enumerate(lines[:50]): 
                line_data = {
                    'line_number': i + 1, 
                    'content': line,
                    'length': len(line),
                    'hex': ' '.join([f'{ord(c):02x}' for c in line[:50]]),  
                }
                
                # Attempt CSV parsing for the line
                try:
                    reader = csv.reader(io.StringIO(line))
                    row = next(reader)
                    line_data['split_by_comma'] = row
                except Exception:
                    line_data['split_by_comma'] = ['Error parsing line']
                
                result['lines'].append(line_data)
            
            break  
        except UnicodeDecodeError:
            logger.warning(f"Inspect CSV: Failed decoding with {encoding}.") 
            continue
    
    if not result['encoding_used']:
        # If all encodings failed, just show byte data
        logger.warning("Inspect CSV: Could not decode with common encodings. Showing hex dump.") 
        file.seek(0)
        byte_data = file.read()
        result['encoding_used'] = 'binary'
        result['hex_dump'] = ' '.join([f'{b:02x}' for b in byte_data[:200]]) 
    
    logger.info("--- Inspect CSV File Finished ---") 
    return Response(result)

# Add DRF viewsets for configuration models
class EmployeeViewSet(DynamicFieldsViewSetMixin, viewsets.ModelViewSet):
    """
    ViewSet for Employee model.
    Supports filtering on all fields and dynamic field selection.
    """
    queryset = Employee.objects.all()
    serializer_class = EmployeeSerializer
    filter_backends = [DjangoFilterBackend, filters.OrderingFilter]
    filterset_fields = '__all__'

class SalaryBandViewSet(DynamicFieldsViewSetMixin, viewsets.ModelViewSet):
    queryset = SalaryBand.objects.all()
    serializer_class = SalaryBandSerializer
    filter_backends = [DjangoFilterBackend, filters.OrderingFilter]
    filterset_fields = '__all__'

class TeamRevenueViewSet(DynamicFieldsViewSetMixin, viewsets.ModelViewSet):
    queryset = TeamRevenue.objects.all()
    serializer_class = TeamRevenueSerializer
    filter_backends = [DjangoFilterBackend, filters.OrderingFilter]
    filterset_fields = '__all__'

class MeritMatrixViewSet(DynamicFieldsViewSetMixin, viewsets.ModelViewSet):
    queryset = MeritMatrix.objects.all()
    serializer_class = MeritMatrixSerializer
    filter_backends = [DjangoFilterBackend, filters.OrderingFilter]
    filterset_fields = '__all__'

class RevenueTrendFactorViewSet(DynamicFieldsViewSetMixin, viewsets.ModelViewSet):
    queryset = RevenueTrendFactor.objects.all()
    serializer_class = RevenueTrendFactorSerializer
    filter_backends = [DjangoFilterBackend, filters.OrderingFilter]
    filterset_fields = '__all__'

class KpiAchievementViewSet(DynamicFieldsViewSetMixin, viewsets.ModelViewSet):
    queryset = KpiAchievement.objects.all()
    serializer_class = KpiAchievementSerializer
    filter_backends = [DjangoFilterBackend, filters.OrderingFilter]
    filterset_fields = '__all__'

class CompensationConfigViewSet(DynamicFieldsViewSetMixin, viewsets.ModelViewSet):
    queryset = CompensationConfig.objects.all()
    serializer_class = CompensationConfigSerializer
    filter_backends = [DjangoFilterBackend, filters.OrderingFilter]
    filterset_fields = '__all__'

class TeamViewSet(DynamicFieldsViewSetMixin, viewsets.ModelViewSet):
    queryset = Team.objects.all()
    serializer_class = TeamSerializer
    filter_backends = [DjangoFilterBackend, filters.OrderingFilter]
    filterset_fields = '__all__'

# Add DRF viewsets for snapshot models
class DataSnapshotViewSet(DynamicFieldsViewSetMixin, viewsets.ModelViewSet):
    queryset = DataSnapshot.objects.all().order_by('-created_at')
    serializer_class = DataSnapshotSerializer
    filter_backends = [DjangoFilterBackend, filters.OrderingFilter]
    filterset_fields = '__all__'

    def get_serializer_class(self):
        if self.action == 'create':
            return DataSnapshotCreateSerializer
        return DataSnapshotSerializer

class ScenarioViewSet(DynamicFieldsViewSetMixin, viewsets.ModelViewSet):
    """
    API endpoint for managing compensation scenarios.
    
    Scenarios allow users to create and save different compensation models
    with specific parameters and employee overrides for comparison.
    """
    queryset = Scenario.objects.all()
    serializer_class = ScenarioSerializer
    filter_backends = [DjangoFilterBackend, filters.OrderingFilter]
    filterset_fields = '__all__'
    ordering_fields = ['name', 'created_at', 'updated_at']
    ordering = ['-created_at']
    
    @action(detail=True, methods=['post'])
    def run(self, request, pk=None):
        """
        Run the scenario and return the results.
        
        This endpoint calculates compensation based on the scenario parameters
        and employee overrides, then returns the results.
        """
        scenario = self.get_object()
        
        # Get parameters from the scenario
        parameters = scenario.parameters or {}
        
        # Use transaction to create temporary objects for calculation
        with transaction.atomic():
            # If scenario has a base snapshot, use employees from that snapshot
            if scenario.base_snapshot:
                # Create temporary employees from the snapshot
                snapshot_employees = EmployeeSnapshot.objects.filter(snapshot=scenario.base_snapshot)
                temp_employees = []
                
                for snapshot in snapshot_employees:
                    # Create a team if needed
                    team_obj = None
                    if snapshot.team:
                        team_obj, _ = Team.objects.get_or_create(id=snapshot.team)
                    
                    # Create temporary employee
                    employee = Employee.objects.create(
                        employee_id=snapshot.employee_id,
                        name=snapshot.name,
                        base_salary=snapshot.base_salary,
                        pool_share=snapshot.pool_share,
                        target_bonus=snapshot.target_bonus,
                        performance_score=snapshot.performance_score,
                        last_year_revenue=snapshot.last_year_revenue,
                        role=snapshot.role,
                        level=snapshot.level,
                        is_mrt=snapshot.is_mrt,
                        performance_rating=snapshot.performance_rating,
                        team=team_obj
                    )
                    
                    # Apply overrides if any
                    override = ScenarioEmployeeOverride.objects.filter(
                        scenario=scenario, 
                        employee__employee_id=snapshot.employee_id
                    ).first()
                    
                    if override:
                        if override.performance_rating:
                            employee.performance_rating = override.performance_rating
                        if override.is_mrt is not None:
                            employee.is_mrt = override.is_mrt
                        if override.base_salary_override:
                            employee.base_salary = override.base_salary_override
                        if override.target_bonus_override:
                            employee.target_bonus = override.target_bonus_override
                    
                    temp_employees.append(employee)
            else:
                # Use current employees
                current_employees = Employee.objects.all()
                temp_employees = []
                
                for emp in current_employees:
                    # Create a copy of the employee
                    employee = Employee.objects.create(
                        employee_id=emp.employee_id,
                        name=emp.name,
                        base_salary=emp.base_salary,
                        pool_share=emp.pool_share,
                        target_bonus=emp.target_bonus,
                        performance_score=emp.performance_score,
                        last_year_revenue=emp.last_year_revenue,
                        role=emp.role,
                        level=emp.level,
                        is_mrt=emp.is_mrt,
                        performance_rating=emp.performance_rating,
                        team=emp.team
                    )
                    
                    # Apply overrides if any
                    override = ScenarioEmployeeOverride.objects.filter(
                        scenario=scenario, 
                        employee=emp
                    ).first()
                    
                    if override:
                        if override.performance_rating:
                            employee.performance_rating = override.performance_rating
                        if override.is_mrt is not None:
                            employee.is_mrt = override.is_mrt
                        if override.base_salary_override:
                            employee.base_salary = override.base_salary_override
                        if override.target_bonus_override:
                            employee.target_bonus = override.target_bonus_override
                    
                    temp_employees.append(employee)
            
            # Extract parameters
            use_proposed_model = parameters.get('use_proposed_model', True)
            revenue_delta = Decimal(str(parameters.get('revenue_delta', 0)))
            adjustment_factor = Decimal(str(parameters.get('adjustment_factor', 1)))
            use_pool_method = parameters.get('use_pool_method', False)
            current_year = int(parameters.get('current_year', 2025))
            performance_rating = parameters.get('performance_rating', 'Meets Expectations')
            is_mrt = parameters.get('is_mrt', False)
            use_overrides = parameters.get('use_overrides', True)
            
            # Run the model
            if use_proposed_model:
                if use_overrides:
                    output = run_proposed_model_for_all(temp_employees, current_year, performance_rating, is_mrt)
                else:
                    output = run_proposed_model_for_all(temp_employees, current_year)
            else:
                output = run_comparison(temp_employees, revenue_delta, adjustment_factor, use_pool_method)
                
            # Apply discretionary adjustments from overrides
            if 'results' in output:
                results = output['results']
                for i, result in enumerate(results):
                    employee_id = None
                    for emp in temp_employees:
                        if emp.name == result['employee']:
                            employee_id = emp.employee_id
                            break
                    
                    if employee_id:
                        original_employee = Employee.objects.filter(employee_id=employee_id).first()
                        if original_employee:
                            override = ScenarioEmployeeOverride.objects.filter(
                                scenario=scenario, 
                                employee=original_employee
                            ).first()
                            
                            if override and override.discretionary_adjustment:
                                adjustment = float(override.discretionary_adjustment) / 100
                                if 'bonus_amount' in result:
                                    bonus = float(result['bonus_amount'])
                                    result['bonus_amount'] = bonus * (1 + adjustment)
                                if 'total_compensation' in result:
                                    total = float(result['total_compensation'])
                                    base = float(result.get('new_salary', result.get('adjusted_base', 0)))
                                    bonus = total - base
                                    adjusted_bonus = bonus * (1 + adjustment)
                                    result['total_compensation'] = base + adjusted_bonus
            
            # Cache the results
            scenario.results_cache = output
            scenario.save()
            
            # Roll back all temporary objects
            transaction.set_rollback(True)
        
        return Response(output)
    
    @action(detail=True, methods=['post'])
    def duplicate(self, request, pk=None):
        """
        Create a duplicate of this scenario with a new name.
        """
        scenario = self.get_object()
        
        # Get new name from request or generate one
        new_name = request.data.get('name', f"{scenario.name} (Copy)")
        
        # Create new scenario
        new_scenario = Scenario.objects.create(
            name=new_name,
            description=scenario.description,
            created_by=scenario.created_by,
            base_snapshot=scenario.base_snapshot,
            parameters=scenario.parameters
        )
        
        # Copy overrides
        for override in ScenarioEmployeeOverride.objects.filter(scenario=scenario):
            ScenarioEmployeeOverride.objects.create(
                scenario=new_scenario,
                employee=override.employee,
                performance_rating=override.performance_rating,
                is_mrt=override.is_mrt,
                base_salary_override=override.base_salary_override,
                target_bonus_override=override.target_bonus_override,
                discretionary_adjustment=override.discretionary_adjustment
            )
        
        serializer = self.get_serializer(new_scenario)
        return Response(serializer.data)
        
    @action(detail=True, methods=['post'])
    def create_version(self, request, pk=None):
        """
        Create a new version of this scenario.
        
        This endpoint creates a new version record with the current parameters and results.
        """
        scenario = self.get_object()
        
        # Get the next version number
        latest_version = ScenarioVersion.objects.filter(scenario=scenario).order_by('-version_number').first()
        version_number = 1
        if latest_version:
            version_number = latest_version.version_number + 1
            
        # Get notes from request
        notes = request.data.get('notes', '')
        created_by = request.data.get('created_by', scenario.created_by)
        
        # Create new version
        version = ScenarioVersion.objects.create(
            scenario=scenario,
            version_number=version_number,
            created_by=created_by,
            parameters=scenario.parameters,
            results_cache=scenario.results_cache,
            notes=notes
        )
        
        serializer = ScenarioVersionSerializer(version)
        return Response(serializer.data)

class ScenarioEmployeeOverrideViewSet(DynamicFieldsViewSetMixin, viewsets.ModelViewSet):
    """
    API endpoint for managing employee-specific overrides within scenarios.
    """
    queryset = ScenarioEmployeeOverride.objects.all()
    serializer_class = ScenarioEmployeeOverrideSerializer
    filter_backends = [DjangoFilterBackend, filters.OrderingFilter]
    filterset_fields = '__all__'

class ScenarioVersionViewSet(DynamicFieldsViewSetMixin, viewsets.ModelViewSet):
    """
    API endpoint for managing scenario versions.
    
    Versions represent snapshots of a scenario's parameters and results at different points in time.
    """
    queryset = ScenarioVersion.objects.all()
    serializer_class = ScenarioVersionSerializer
    filter_backends = [DjangoFilterBackend, filters.OrderingFilter]
    filterset_fields = '__all__'
    
    @action(detail=True, methods=['post'])
    def restore(self, request, pk=None):
        """
        Restore this version to the parent scenario.
        
        This endpoint copies the parameters and results from this version back to the parent scenario.
        """
        version = self.get_object()
        scenario = version.scenario
        
        # Copy parameters and results back to scenario
        scenario.parameters = version.parameters
        scenario.results_cache = version.results_cache
        scenario.save()
        
        serializer = ScenarioSerializer(scenario)
        return Response(serializer.data)

class ScenarioComparisonViewSet(DynamicFieldsViewSetMixin, viewsets.ModelViewSet):
    """
    API endpoint for managing scenario comparisons.
    
    Comparisons allow users to compare multiple scenarios or versions side by side.
    """
    queryset = ScenarioComparison.objects.all()
    serializer_class = ScenarioComparisonSerializer
    filter_backends = [DjangoFilterBackend, filters.OrderingFilter]
    filterset_fields = '__all__'
    
    @action(detail=True, methods=['post'])
    def run(self, request, pk=None):
        """
        Run the comparison and return the results.
        
        This endpoint runs all scenarios in the comparison and returns the combined results.
        """
        comparison = self.get_object()
        
        # Run the primary scenario
        primary_scenario = comparison.primary_scenario
        primary_version = comparison.primary_version
        
        # If a specific version is selected, use its cached results
        if primary_version and primary_version.results_cache:
            primary_results = primary_version.results_cache
        else:
            # Otherwise run the scenario
            primary_response = self.run_scenario(primary_scenario)
            primary_results = primary_response.data
        
        # Run all comparison scenarios
        comparison_results = []
        for item in ComparisonItem.objects.filter(comparison=comparison):
            scenario = item.scenario
            version = item.version
            
            # If a specific version is selected, use its cached results
            if version and version.results_cache:
                scenario_results = version.results_cache
            else:
                # Otherwise run the scenario
                scenario_response = self.run_scenario(scenario)
                scenario_results = scenario_response.data
                
            # Add scenario info to results
            scenario_info = {
                'scenario_id': scenario.id,
                'scenario_name': scenario.name,
                'version_id': version.id if version else None,
                'version_number': version.version_number if version else None,
                'results': scenario_results
            }
            comparison_results.append(scenario_info)
        
        # Combine results
        output = {
            'primary': {
                'scenario_id': primary_scenario.id,
                'scenario_name': primary_scenario.name,
                'version_id': primary_version.id if primary_version else None,
                'version_number': primary_version.version_number if primary_version else None,
                'results': primary_results
            },
            'comparisons': comparison_results
        }
        
        # Cache the results
        comparison.results_cache = output
        comparison.save()
        
        return Response(output)
    
    def run_scenario(self, scenario):
        """Helper method to run a scenario and return the results."""
        viewset = ScenarioViewSet()
        viewset.request = self.request
        viewset.format_kwarg = self.format_kwarg
        viewset.kwargs = {'pk': scenario.pk}
        viewset.action = 'run'
        return viewset.run(self.request, pk=scenario.pk)

class ComparisonItemViewSet(DynamicFieldsViewSetMixin, viewsets.ModelViewSet):
    """
    API endpoint for managing comparison items.
    
    Comparison items represent individual scenarios or versions within a comparison.
    """
    queryset = ComparisonItem.objects.all()
    serializer_class = ComparisonItemSerializer
    filter_backends = [DjangoFilterBackend, filters.OrderingFilter]
    filterset_fields = '__all__'

@api_view(['POST'])
def create_snapshot(request):
    """Create a snapshot of all current data"""
    try:
        # Get snapshot metadata
        name = request.data.get('name')
        description = request.data.get('description', '')
        created_by = request.data.get('created_by', '')
        
        if not name:
            return Response({'error': 'Snapshot name is required'}, status=400)
        
        # Create the snapshot
        with transaction.atomic():
            snapshot = DataSnapshot.objects.create(
                name=name,
                description=description,
                created_by=created_by
            )
            
            # Snapshot all employees
            employees = Employee.objects.all()
            for employee in employees:
                EmployeeSnapshot.objects.create(
                    snapshot=snapshot,
                    employee_id=employee.employee_id,
                    name=employee.name,
                    base_salary=employee.base_salary,
                    pool_share=employee.pool_share,
                    target_bonus=employee.target_bonus,
                    performance_score=employee.performance_score,
                    last_year_revenue=employee.last_year_revenue,
                    role=employee.role,
                    level=employee.level,
                    is_mrt=employee.is_mrt,
                    performance_rating=employee.performance_rating,
                    team=employee.team.id if employee.team else None
                )
            
            # Snapshot all configuration models
            # SalaryBands
            salary_bands = SalaryBand.objects.all()
            if salary_bands.exists():
                ConfigSnapshot.objects.create(
                    snapshot=snapshot,
                    config_type='salary_band',
                    data=list(salary_bands.values())
                )
            
            # MeritMatrix
            merit_matrices = MeritMatrix.objects.all()
            if merit_matrices.exists():
                ConfigSnapshot.objects.create(
                    snapshot=snapshot,
                    config_type='merit_matrix',
                    data=list(merit_matrices.values())
                )
            
            # TeamRevenue
            team_revenues = TeamRevenue.objects.all()
            if team_revenues.exists():
                ConfigSnapshot.objects.create(
                    snapshot=snapshot,
                    config_type='team_revenue',
                    data=list(team_revenues.values())
                )
            
            # RevenueTrendFactor
            revenue_trend_factors = RevenueTrendFactor.objects.all()
            if revenue_trend_factors.exists():
                ConfigSnapshot.objects.create(
                    snapshot=snapshot,
                    config_type='revenue_trend_factor',
                    data=list(revenue_trend_factors.values())
                )
            
            # KpiAchievement
            kpi_achievements = KpiAchievement.objects.all()
            if kpi_achievements.exists():
                ConfigSnapshot.objects.create(
                    snapshot=snapshot,
                    config_type='kpi_achievement',
                    data=list(kpi_achievements.values())
                )
            
            # Teams
            teams = Team.objects.all()
            if teams.exists():
                ConfigSnapshot.objects.create(
                    snapshot=snapshot,
                    config_type='team',
                    data=list(teams.values())
                )
            
            # CompensationConfig
            compensation_configs = CompensationConfig.objects.all()
            if compensation_configs.exists():
                ConfigSnapshot.objects.create(
                    snapshot=snapshot,
                    config_type='compensation_config',
                    data=list(compensation_configs.values())
                )
        
        return Response({
            'id': snapshot.id,
            'name': snapshot.name,
            'created_at': snapshot.created_at
        }, status=201)
    
    except Exception as e:
        return Response({'error': str(e)}, status=400)

@api_view(['POST'])
def restore_snapshot(request, snapshot_id):
    """Restore data from a snapshot"""
    try:
        snapshot = DataSnapshot.objects.get(pk=snapshot_id)
        
        # Confirm restoration
        confirm = request.data.get('confirm', False)
        if not confirm:
            return Response({
                'message': 'This will replace all current data with the snapshot data. Set confirm=true to proceed.',
                'snapshot': {
                    'id': snapshot.id,
                    'name': snapshot.name,
                    'created_at': snapshot.created_at
                }
            })
        
        with transaction.atomic():
            # Restore employees
            # First, get all current employees to track which ones to delete
            current_employee_ids = set(Employee.objects.values_list('id', flat=True))
            restored_employee_ids = set()
            
            for emp_snapshot in snapshot.employees.all():
                # Try to find by employee_id first if available
                if emp_snapshot.employee_id:
                    employee, created = Employee.objects.update_or_create(
                        employee_id=emp_snapshot.employee_id, 
                        defaults={**emp_snapshot.__dict__, 'name': emp_snapshot.name}
                    )
                else:
                    # If no employee_id, try by name
                    employee, created = Employee.objects.update_or_create(name=emp_snapshot.name, defaults=emp_snapshot.__dict__)
                
                restored_employee_ids.add(employee.id)
            
            # Delete employees that weren't in the snapshot
            employees_to_delete = current_employee_ids - restored_employee_ids
            Employee.objects.filter(id__in=employees_to_delete).delete()
            
            # Restore configuration data
            for config_snapshot in snapshot.configs.all():
                config_type = config_snapshot.config_type
                config_data = config_snapshot.data
                
                if config_type == 'salary_band':
                    # Clear existing
                    SalaryBand.objects.all().delete()
                    # Restore from snapshot
                    for item in config_data:
                        # Remove id to create new records
                        if 'id' in item:
                            del item['id']
                        SalaryBand.objects.create(**item)
                
                elif config_type == 'merit_matrix':
                    MeritMatrix.objects.all().delete()
                    for item in config_data:
                        if 'id' in item:
                            del item['id']
                        MeritMatrix.objects.create(**item)
                
                elif config_type == 'team_revenue':
                    TeamRevenue.objects.all().delete()
                    for item in config_data:
                        if 'id' in item:
                            del item['id']
                        TeamRevenue.objects.create(**item)
                
                elif config_type == 'revenue_trend_factor':
                    RevenueTrendFactor.objects.all().delete()
                    for item in config_data:
                        if 'id' in item:
                            del item['id']
                        RevenueTrendFactor.objects.create(**item)
                
                elif config_type == 'kpi_achievement':
                    KpiAchievement.objects.all().delete()
                    for item in config_data:
                        if 'id' in item:
                            del item['id']
                        KpiAchievement.objects.create(**item)
                
                elif config_type == 'team':
                    Team.objects.all().delete()
                    for item in config_data:
                        if 'id' in item:
                            del item['id']
                        Team.objects.create(**item)
                
                elif config_type == 'compensation_config':
                    CompensationConfig.objects.all().delete()
                    for item in config_data:
                        if 'id' in item:
                            del item['id']
                        CompensationConfig.objects.create(**item)
        
        return Response({'message': f'Successfully restored data from snapshot: {snapshot.name}'})
    
    except DataSnapshot.DoesNotExist:
        return Response({'error': 'Snapshot not found'}, status=404)
    except Exception as e:
        return Response({'error': str(e)}, status=400)

@api_view(['GET'])
def debug_merit_matrix(request):
    """Debug endpoint to check merit matrix in the database"""
    try:
        # Get all merit matrix entries
        merit_matrix = MeritMatrix.objects.all()
        print(f"Found {merit_matrix.count()} merit matrix entries in the database:")
        
        for entry in merit_matrix:
            print(f"  - {entry.performance_rating} / {entry.compa_ratio_range}: {entry.increase_percentage}")
        
        # Return the data
        from rest_framework import serializers
        
        class DebugMeritMatrixSerializer(serializers.ModelSerializer):
            class Meta:
                model = MeritMatrix
                fields = '__all__'
        
        serializer = DebugMeritMatrixSerializer(merit_matrix, many=True)
        return Response(serializer.data)
    except Exception as e:
        print(f"Error in debug_merit_matrix: {str(e)}")
        return Response({'error': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

@api_view(['GET'])
def debug_salary_bands(request):
    """Debug endpoint to check salary bands in the database"""
    try:
        # Get all salary bands
        salary_bands = SalaryBand.objects.all()
        print(f"Found {salary_bands.count()} salary bands in the database:")
        
        for band in salary_bands:
            print(f"  - {band.role} (Level: {band.level}): Min={band.min_value}, Mid={band.mid_value}, Max={band.max_value}")
        
        # Return the data
        from rest_framework import serializers
        
        class DebugSalaryBandSerializer(serializers.ModelSerializer):
            class Meta:
                model = SalaryBand
                fields = '__all__'
        
        serializer = DebugSalaryBandSerializer(salary_bands, many=True)
        return Response(serializer.data)
    except Exception as e:
        print(f"Error in debug_salary_bands: {str(e)}")
        return Response({'error': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
