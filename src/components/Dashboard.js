import React, { useState, useEffect } from 'react';
import { Box, Typography, Button, Grid, Paper, Card, CardContent, CardHeader, Divider, LinearProgress } from '@mui/material';
import {
  PieChart,
  Pie,
  Cell,
  ResponsiveContainer,
  Tooltip,
  Legend,
} from 'recharts';
import ScenarioControls from './ScenarioControls';
import ProposedModelControls from './ProposedModelControls';
import ResultsDisplay from './ResultsDisplay';
import api from '../services/api';

const Dashboard = () => {
  const [revenueDelta, setRevenueDelta] = useState(0);
  const [adjustmentFactor, setAdjustmentFactor] = useState(1);
  const [usePoolMethod, setUsePoolMethod] = useState(false);
  const [useProposedModel, setUseProposedModel] = useState(false);
  const [performanceRating, setPerformanceRating] = useState('Meets Expectations');
  const [currentYear, setCurrentYear] = useState(2025);
  const [isMrt, setIsMrt] = useState(false);
  const [useOverrides, setUseOverrides] = useState(false); // Default to OFF
  const [results, setResults] = useState([]);
  const [summary, setSummary] = useState({ total_model_a: '0.00', total_model_b: '0.00' });
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);

  const [summaryData, setSummaryData] = useState({
    totalEmployees: 0,
    totalBaseSalary: 0,
    averagePerformance: 0,
    totalBonus: 0,
  });
  const [employeeData, setEmployeeData] = useState([]);
  const [bonusDistribution, setBonusDistribution] = useState([]);
  const [teamBreakdown, setTeamBreakdown] = useState([]);

  const fetchDashboardData = async () => {
    try {
      const employeesResponse = await api.get('/employees/');
      const employees = employeesResponse.data;

      // Calculate summary data
      const totalEmployees = employees.length;
      const totalBaseSalary = employees.reduce((sum, emp) => sum + parseFloat(emp.base_salary), 0);
      const averagePerformance = employees.reduce((sum, emp) => sum + parseFloat(emp.performance_score), 0) / totalEmployees;
      const totalBonus = employees.reduce((sum, emp) => sum + parseFloat(emp.target_bonus), 0);

      setSummaryData({
        totalEmployees,
        totalBaseSalary,
        averagePerformance,
        totalBonus,
      });

      // Prepare data for bar chart
      const sortedEmployees = [...employees]
        .sort((a, b) => parseFloat(b.target_bonus) - parseFloat(a.target_bonus))
        .slice(0, 5);
      setEmployeeData(sortedEmployees);

      // Prepare data for pie chart
      const bonusRanges = {
        'Under 50k': 0,
        '50k-100k': 0,
        '100k-200k': 0,
        'Over 200k': 0,
      };

      employees.forEach(emp => {
        const bonus = parseFloat(emp.target_bonus);
        if (bonus < 50000) bonusRanges['Under 50k']++;
        else if (bonus < 100000) bonusRanges['50k-100k']++;
        else if (bonus < 200000) bonusRanges['100k-200k']++;
        else bonusRanges['Over 200k']++;
      });

      setBonusDistribution(Object.entries(bonusRanges).map(([name, value]) => ({
        name,
        value,
      })));
    } catch (error) {
      console.error('Error fetching dashboard data:', error);
    }
  };

  useEffect(() => {
    fetchDashboardData();
  }, []);

  const COLORS = ['#0088FE', '#00C49F', '#FFBB28', '#FF8042'];

  const formatCurrency = (value) => {
    return new Intl.NumberFormat('en-US', {
      style: 'currency',
      currency: 'USD',
      minimumFractionDigits: 0,
      maximumFractionDigits: 0,
    }).format(value);
  };

  const handleRun = async () => {
    setLoading(true);
    setError(null);
    try {
      console.log('Sending request to API with params:', {
        revenue_delta: revenueDelta,
        adjustment_factor: adjustmentFactor,
        use_pool_method: usePoolMethod,
        use_proposed_model: useProposedModel,
        current_year: currentYear,
        performance_rating: performanceRating,
        is_mrt: isMrt,
        use_overrides: useOverrides,
      });
      const { data } = await api.post('/calculate/', {
        revenue_delta: revenueDelta,
        adjustment_factor: adjustmentFactor,
        use_pool_method: usePoolMethod,
        use_proposed_model: useProposedModel,
        current_year: currentYear,
        performance_rating: performanceRating,
        is_mrt: isMrt,
        use_overrides: useOverrides,
      });
      console.log('API Response (results):', data.results);
      setResults(data.results);
      setSummary(data.summary);

      // Generate team breakdown data for visualization
      if (useProposedModel && data.results.length > 0) {
        // Group results by team
        const teamData = {};
        data.results.forEach(employee => {
          const team = employee.team || 'Unassigned';
          if (!teamData[team]) {
            teamData[team] = {
              team,
              salary: 0,
              bonus: 0,
              total: 0,
              employeeCount: 0
            };
          }
          
          // Parse values to ensure they're numbers - handle both string and number formats
          let salary = 0;
          let bonus = 0;
          
          // Handle new_salary - could be string with currency formatting or number
          if (typeof employee.new_salary === 'string') {
            salary = parseFloat(employee.new_salary.replace(/[^0-9.-]+/g, ''));
          } else if (typeof employee.new_salary === 'number') {
            salary = employee.new_salary;
          }
          
          // Handle bonus_amount - could be string with currency formatting or number
          if (typeof employee.bonus_amount === 'string') {
            bonus = parseFloat(employee.bonus_amount.replace(/[^0-9.-]+/g, ''));
          } else if (typeof employee.bonus_amount === 'number') {
            bonus = employee.bonus_amount;
          }
          
          // Handle NaN cases
          salary = isNaN(salary) ? 0 : salary;
          bonus = isNaN(bonus) ? 0 : bonus;
          
          teamData[team].salary += salary;
          teamData[team].bonus += bonus;
          teamData[team].total += (salary + bonus);
          teamData[team].employeeCount += 1;
        });

        // Convert to array and sort by total compensation
        const sortedTeamData = Object.values(teamData).sort((a, b) => b.total - a.total);
        setTeamBreakdown(sortedTeamData);
      } else {
        setTeamBreakdown([]);
      }
    } catch (err) {
      console.error('Error running simulation:', err);
      if (err.message === 'Network Error') {
        setError('Network Error: Unable to connect to the backend server. Please make sure the Django server is running on port 8000.');
      } else {
        setError(err.response?.data?.error || err.message || 'An unknown error occurred');
      }
    }
    setLoading(false);
  };

  return (
    <Box>
      <Typography variant="h4" component="h1" gutterBottom>
        Dashboard
      </Typography>

      <Grid container spacing={3}>
        {/* Summary Cards */}
        <Grid item xs={12} sm={6} md={3}>
          <Card sx={{ bgcolor: 'grey.800', height: '100%' }}>
            <CardContent sx={{ p: 3, display: 'flex', flexDirection: 'column', justifyContent: 'center' }}>
              <Typography color="text.secondary" variant="subtitle1" gutterBottom>
                Total Employees
              </Typography>
              <Typography variant="h3" sx={{ fontWeight: 'bold' }}>
                {summaryData.totalEmployees}
              </Typography>
            </CardContent>
          </Card>
        </Grid>
        <Grid item xs={12} sm={6} md={3}>
          <Card sx={{ bgcolor: 'grey.800', height: '100%' }}>
            <CardContent sx={{ p: 3, display: 'flex', flexDirection: 'column', justifyContent: 'center' }}>
              <Typography color="text.secondary" variant="subtitle1" gutterBottom>
                Total Base Salary
              </Typography>
              <Typography variant="h3" sx={{ fontWeight: 'bold' }}>
                {formatCurrency(summaryData.totalBaseSalary)}
              </Typography>
            </CardContent>
          </Card>
        </Grid>
        <Grid item xs={12} sm={6} md={3}>
          <Card sx={{ bgcolor: 'grey.800', height: '100%' }}>
            <CardContent sx={{ p: 3, display: 'flex', flexDirection: 'column', justifyContent: 'center' }}>
              <Typography color="text.secondary" variant="subtitle1" gutterBottom>
                Average Performance
              </Typography>
              <Typography variant="h3" sx={{ fontWeight: 'bold' }}>
                {(summaryData.averagePerformance * 100).toFixed(1)}%
              </Typography>
            </CardContent>
          </Card>
        </Grid>
        <Grid item xs={12} sm={6} md={3}>
          <Card sx={{ bgcolor: 'grey.800', height: '100%' }}>
            <CardContent sx={{ p: 3, display: 'flex', flexDirection: 'column', justifyContent: 'center' }}>
              <Typography color="text.secondary" variant="subtitle1" gutterBottom>
                Total Target Bonus
              </Typography>
              <Typography variant="h3" sx={{ fontWeight: 'bold' }}>
                {formatCurrency(summaryData.totalBonus)}
              </Typography>
            </CardContent>
          </Card>
        </Grid>

        {/* Charts */}
        <Grid item xs={12} md={8}>
          <Paper sx={{ p: 2 }}>
            <Typography variant="h6" gutterBottom>
              Top 5 Employee Bonuses
            </Typography>
            <Box sx={{ width: '100%', height: 300 }}>
              {employeeData.length > 0 && (
                <ResponsiveContainer>
                  <PieChart>
                    <Pie
                      data={employeeData}
                      cx="50%"
                      cy="50%"
                      labelLine={false}
                      label={({ name, percent }) => `${name} (${(percent * 100).toFixed(0)}%)`}
                      outerRadius={80}
                      fill="#8884d8"
                      dataKey="target_bonus"
                    >
                      {employeeData.map((entry, index) => (
                        <Cell key={`cell-${index}`} fill={COLORS[index % COLORS.length]} />
                      ))}
                    </Pie>
                    <Tooltip />
                    <Legend />
                  </PieChart>
                </ResponsiveContainer>
              )}
            </Box>
          </Paper>
        </Grid>

        <Grid item xs={12} md={4}>
          <Paper sx={{ p: 2, height: '100%' }}>
            <Typography variant="h6" gutterBottom>
              Bonus Distribution
            </Typography>
            <Box sx={{ width: '100%', height: 300 }}>
              <ResponsiveContainer>
                <PieChart>
                  <Pie
                    data={bonusDistribution}
                    cx="50%"
                    cy="50%"
                    labelLine={false}
                    label={({ name, percent }) => `${name} (${(percent * 100).toFixed(0)}%)`}
                    outerRadius={80}
                    fill="#8884d8"
                    dataKey="value"
                  >
                    {bonusDistribution.map((entry, index) => (
                      <Cell key={`cell-${index}`} fill={COLORS[index % COLORS.length]} />
                    ))}
                  </Pie>
                  <Tooltip />
                  <Legend />
                </PieChart>
              </ResponsiveContainer>
            </Box>
          </Paper>
        </Grid>

        {/* Team Breakdown Cards - Always shown, moved up from bottom */}
        {teamBreakdown.length > 0 && (
          <Grid item xs={12}>
            <Paper sx={{ p: 2, mb: 3 }}>
              <Typography variant="h6" gutterBottom>Team Compensation Breakdown</Typography>
              <Grid container spacing={2}>
                {teamBreakdown.map(team => {
                  const salaryPercentage = (team.salary / team.total) * 100;
                  const bonusPercentage = (team.bonus / team.total) * 100;
                  
                  return (
                    <Grid item xs={12} sm={6} md={4} lg={3} key={team.team}>
                      <Card sx={{ bgcolor: 'grey.800', height: '100%' }}>
                        <CardContent>
                          <Box display="flex" justifyContent="space-between" alignItems="center" mb={1}>
                            <Typography variant="h6">{team.team}</Typography>
                            <Typography variant="body2" color="text.secondary">
                              {team.employeeCount} employees
                            </Typography>
                          </Box>
                          
                          <Box mb={1.5}>
                            <Box display="flex" justifyContent="space-between" mb={0.5}>
                              <Typography variant="body2">Base Salary</Typography>
                              <Typography variant="body2">{formatCurrency(team.salary)}</Typography>
                            </Box>
                            <LinearProgress 
                              variant="determinate" 
                              value={100} 
                              sx={{ 
                                height: 8, 
                                borderRadius: 4, 
                                backgroundColor: 'rgba(136, 132, 216, 0.3)',
                                '& .MuiLinearProgress-bar': {
                                  backgroundColor: '#8884d8',
                                }
                              }} 
                            />
                          </Box>
                          
                          <Box mb={1.5}>
                            <Box display="flex" justifyContent="space-between" mb={0.5}>
                              <Typography variant="body2">Bonus</Typography>
                              <Typography variant="body2">{formatCurrency(team.bonus)}</Typography>
                            </Box>
                            <LinearProgress 
                              variant="determinate" 
                              value={100} 
                              sx={{ 
                                height: 8, 
                                borderRadius: 4, 
                                backgroundColor: 'rgba(130, 202, 157, 0.3)',
                                '& .MuiLinearProgress-bar': {
                                  backgroundColor: '#82ca9d',
                                }
                              }} 
                            />
                          </Box>
                          
                          <Box display="flex" justifyContent="space-between" alignItems="center">
                            <Typography variant="body1" fontWeight="bold">Total</Typography>
                            <Typography variant="body1" fontWeight="bold">
                              {formatCurrency(team.total)}
                            </Typography>
                          </Box>
                          
                          <Box display="flex" mt={1} height={10}>
                            <Box 
                              width={`${salaryPercentage}%`} 
                              bgcolor="#8884d8" 
                              borderRadius={salaryPercentage > 95 ? "4px" : "4px 0 0 4px"}
                            />
                            <Box 
                              width={`${bonusPercentage}%`} 
                              bgcolor="#82ca9d" 
                              borderRadius={bonusPercentage > 95 ? "4px" : "0 4px 4px 0"}
                            />
                          </Box>
                          <Box display="flex" justifyContent="space-between" mt={0.5}>
                            <Typography variant="caption" color="text.secondary">
                              Salary: {salaryPercentage.toFixed(1)}%
                            </Typography>
                            <Typography variant="caption" color="text.secondary">
                              Bonus: {bonusPercentage.toFixed(1)}%
                            </Typography>
                          </Box>
                        </CardContent>
                      </Card>
                    </Grid>
                  );
                })}
              </Grid>
            </Paper>
          </Grid>
        )}

        <Grid item xs={12}>
          <Box p={2} mb={4} border={1} borderColor="grey.300" borderRadius={2}>
            <Typography variant="h6" gutterBottom>
              Scenario & Results
            </Typography>
            <Box mt={2} mb={2}>
              <Button
                variant="outlined"
                onClick={() => setUseProposedModel(!useProposedModel)}
                color={useProposedModel ? "primary" : "inherit"}
              >
                {useProposedModel ? "Using Proposed Model" : "Using Original Model"}
              </Button>
            </Box>

            {useProposedModel ? (
              <ProposedModelControls
                performanceRating={performanceRating}
                setPerformanceRating={setPerformanceRating}
                currentYear={currentYear}
                setCurrentYear={setCurrentYear}
                isMrt={isMrt}
                setIsMrt={setIsMrt}
                useOverrides={useOverrides}
                setUseOverrides={setUseOverrides}
              />
            ) : (
              <ScenarioControls
                revenueDelta={revenueDelta}
                setRevenueDelta={setRevenueDelta}
                adjustmentFactor={adjustmentFactor}
                setAdjustmentFactor={setAdjustmentFactor}
                usePoolMethod={usePoolMethod}
                setUsePoolMethod={setUsePoolMethod}
              />
            )}
            <Box mt={2}>
              <Button
                variant="contained"
                onClick={handleRun}
                disabled={loading}
              >
                {loading ? 'Running...' : 'Run Simulation'}
              </Button>
            </Box>
            {error && <Typography color="error" mt={2}>{error}</Typography>}
            {results.length > 0 && <ResultsDisplay results={results} summary={summary} />}
          </Box>
        </Grid>
      </Grid>
    </Box>
  );
};

export default Dashboard;
