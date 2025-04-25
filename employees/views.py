# DRF ping endpoint
from rest_framework.decorators import api_view
from rest_framework.response import Response
from decimal import Decimal
import csv
from .models import Employee, SalaryBand, TeamRevenue, MeritMatrix, RevenueTrendFactor, KpiAchievement, Team, CompensationConfig, DataSnapshot, EmployeeSnapshot, ConfigSnapshot
from .serializers import (
    EmployeeSerializer, SalaryBandSerializer, TeamRevenueSerializer, MeritMatrixSerializer, 
    RevenueTrendFactorSerializer, KpiAchievementSerializer, CompensationConfigSerializer,
    DataSnapshotSerializer, DataSnapshotCreateSerializer, TeamSerializer
)
from .compensation_engine import run_comparison
from .merit_engine import run_proposed_model_for_all
from rest_framework import status, viewsets
from rest_framework.views import APIView
from rest_framework.parsers import MultiPartParser
from django.db import transaction

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
                    data['employee_id'] = int(row['employee_id'])
                    # Use employee_id for lookup if available
                    emp, created_flag = Employee.objects.update_or_create(
                        employee_id=data['employee_id'], 
                        defaults={**data, 'name': row['name']}
                    )
                except ValueError:
                    return Response({'error': f'Invalid employee_id in row {idx}: {row["employee_id"]}'}, status=400)
            else:
                # Fall back to using name for lookup
                emp, created_flag = Employee.objects.update_or_create(name=row['name'], defaults=data)
            
            # Debug: Print processed data
            print(f"PROCESSED DATA: {data}")
            
            # Debug: Print employee after save
            print(f"SAVED EMPLOYEE: {emp.name}, Rating: {emp.performance_rating}, MRT: {emp.is_mrt}")
            
            if created_flag:
                created.append(emp.name)
            else:
                updated.append(emp.name)
        except Exception as e:
            print(f"ERROR processing row {idx}: {str(e)}")
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

# CSV upload for Team master data
class TeamUploadView(APIView):
    parser_classes = [MultiPartParser]
    def post(self, request, format=None):
        print("TeamUploadView.post called")
        file = request.FILES.get('file')
        if not file:
            print("No file provided")
            return Response({'detail':'No file provided'}, status=status.HTTP_400_BAD_REQUEST)
        
        try:
            print(f"Processing file: {file.name}, size: {file.size}")
            # Read file content
            content = file.read()
            print(f"Read {len(content)} bytes")
            
            # Try to decode with different encodings
            try:
                data = content.decode('utf-8').splitlines()
                print(f"Decoded with UTF-8, got {len(data)} lines")
            except UnicodeDecodeError:
                print("UTF-8 decode failed, trying latin-1")
                try:
                    data = content.decode('latin-1').splitlines()
                    print(f"Decoded with latin-1, got {len(data)} lines")
                except UnicodeDecodeError:
                    print("Failed to decode file with any encoding")
                    return Response({'detail': 'Unable to decode file. Please ensure it is a valid CSV file.'}, 
                                   status=status.HTTP_400_BAD_REQUEST)
            
            # Parse CSV
            if not data:
                print("File is empty")
                return Response({'detail': 'File is empty'}, status=status.HTTP_400_BAD_REQUEST)
            
            print(f"CSV data first 5 lines: {data[:5]}") # Added logging
            reader = csv.DictReader(data)
            
            # Check if reader.fieldnames is None (happens with malformed CSV)
            if not reader.fieldnames:
                print("No fieldnames detected in CSV") # Added logging
                return Response({'detail': 'Invalid CSV format. Could not detect headers.'}, 
                               status=status.HTTP_400_BAD_REQUEST)
            
            print(f"CSV fieldnames detected: {reader.fieldnames}") # Added logging
            
            # Validate CSV structure
            if 'name' not in reader.fieldnames:
                print(f"'name' column not found in fieldnames: {reader.fieldnames}")
                return Response({
                    'detail': f'CSV file must have a "name" column. Found columns: {", ".join(reader.fieldnames)}'
                }, status=status.HTTP_400_BAD_REQUEST)
            
            # Clear existing teams
            Team.objects.all().delete()
            print("Deleted existing teams")
            
            # Process rows
            errors = []
            success_count = 0
            
            for idx, row in enumerate(reader, start=1):
                print(f"Processing row {idx}: {row}")
                name_val = row.get('name', '').strip()
                if not name_val:
                    print(f"Row {idx}: Missing or empty name value")
                    errors.append({'row': idx, 'errors': 'Missing or empty name value'})
                    continue
                try:
                    Team.objects.create(name=name_val)
                    success_count += 1
                    print(f"Created team: {name_val}")
                except Exception as e:
                    print(f"Error creating team at row {idx}: {str(e)}")
                    errors.append({'row': idx, 'errors': str(e)})
            
            if errors and success_count == 0:
                print(f"Failed to import any teams. {len(errors)} errors.")
                return Response({
                    'errors': errors,
                    'detail': f'Failed to import any teams. Found {len(errors)} errors.'
                }, status=status.HTTP_400_BAD_REQUEST)
            elif errors:
                print(f"Imported {success_count} teams with {len(errors)} errors.")
                return Response({
                    'errors': errors,
                    'detail': f'Imported {success_count} teams with {len(errors)} errors.'
                }, status=status.HTTP_207_MULTI_STATUS)
            
            print(f"Successfully imported {success_count} teams.")
            return Response({
                'detail': f'Successfully imported {success_count} teams.'
            }, status=status.HTTP_201_CREATED)
            
        except csv.Error as e:
            print(f"CSV parsing error: {str(e)}")
            return Response({
                'detail': f'CSV parsing error: {str(e)}'
            }, status=status.HTTP_400_BAD_REQUEST)
        except Exception as e:
            print(f"Unexpected error: {str(e)}")
            import traceback
            traceback.print_exc()
            return Response({
                'detail': f'Error processing file: {str(e)}'
            }, status=status.HTTP_400_BAD_REQUEST)

# Add DRF viewsets for configuration models
class SalaryBandViewSet(viewsets.ModelViewSet):
    queryset = SalaryBand.objects.all()
    serializer_class = SalaryBandSerializer

class TeamRevenueViewSet(viewsets.ModelViewSet):
    queryset = TeamRevenue.objects.all()
    serializer_class = TeamRevenueSerializer

class MeritMatrixViewSet(viewsets.ModelViewSet):
    queryset = MeritMatrix.objects.all()
    serializer_class = MeritMatrixSerializer

class RevenueTrendFactorViewSet(viewsets.ModelViewSet):
    queryset = RevenueTrendFactor.objects.all()
    serializer_class = RevenueTrendFactorSerializer

class KpiAchievementViewSet(viewsets.ModelViewSet):
    queryset = KpiAchievement.objects.all()
    serializer_class = KpiAchievementSerializer

class CompensationConfigViewSet(viewsets.ModelViewSet):
    queryset = CompensationConfig.objects.all()
    serializer_class = CompensationConfigSerializer
    
class TeamViewSet(viewsets.ModelViewSet):
    queryset = Team.objects.all()
    serializer_class = TeamSerializer

# Add DRF viewsets for snapshot models
class DataSnapshotViewSet(viewsets.ModelViewSet):
    queryset = DataSnapshot.objects.all().order_by('-created_at')
    serializer_class = DataSnapshotSerializer

    def get_serializer_class(self):
        if self.action == 'create':
            return DataSnapshotCreateSerializer
        return DataSnapshotSerializer

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
                        defaults={
                            'name': emp_snapshot.name,
                            'base_salary': emp_snapshot.base_salary,
                            'pool_share': emp_snapshot.pool_share,
                            'target_bonus': emp_snapshot.target_bonus,
                            'performance_score': emp_snapshot.performance_score,
                            'last_year_revenue': emp_snapshot.last_year_revenue,
                            'role': emp_snapshot.role,
                            'level': emp_snapshot.level,
                            'is_mrt': emp_snapshot.is_mrt,
                            'performance_rating': emp_snapshot.performance_rating,
                            'team_id': emp_snapshot.team
                        }
                    )
                else:
                    # If no employee_id, try by name
                    employee, created = Employee.objects.update_or_create(
                        name=emp_snapshot.name,
                        defaults={
                            'base_salary': emp_snapshot.base_salary,
                            'pool_share': emp_snapshot.pool_share,
                            'target_bonus': emp_snapshot.target_bonus,
                            'performance_score': emp_snapshot.performance_score,
                            'last_year_revenue': emp_snapshot.last_year_revenue,
                            'role': emp_snapshot.role,
                            'level': emp_snapshot.level,
                            'is_mrt': emp_snapshot.is_mrt,
                            'performance_rating': emp_snapshot.performance_rating,
                            'team_id': emp_snapshot.team
                        }
                    )
                
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
