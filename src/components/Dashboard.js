import React, { useState, useEffect } from 'react';
import { Box, Typography, Button, Grid, Paper, Card, CardContent, CardHeader, Divider } from '@mui/material';
import { BarChart } from '@mui/x-charts';
import {
  PieChart,
  Pie,
  Cell,
  ResponsiveContainer,
  Tooltip,
  Legend
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
    } catch (err) {
      setError(err.response?.data?.error || err.message);
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
          <Card>
            <CardContent>
              <Typography color="textSecondary" gutterBottom>
                Total Employees
              </Typography>
              <Typography variant="h4">
                {summaryData.totalEmployees}
              </Typography>
            </CardContent>
          </Card>
        </Grid>
        <Grid item xs={12} sm={6} md={3}>
          <Card>
            <CardContent>
              <Typography color="textSecondary" gutterBottom>
                Total Base Salary
              </Typography>
              <Typography variant="h4">
                {formatCurrency(summaryData.totalBaseSalary)}
              </Typography>
            </CardContent>
          </Card>
        </Grid>
        <Grid item xs={12} sm={6} md={3}>
          <Card>
            <CardContent>
              <Typography color="textSecondary" gutterBottom>
                Average Performance
              </Typography>
              <Typography variant="h4">
                {(summaryData.averagePerformance * 100).toFixed(1)}%
              </Typography>
            </CardContent>
          </Card>
        </Grid>
        <Grid item xs={12} sm={6} md={3}>
          <Card>
            <CardContent>
              <Typography color="textSecondary" gutterBottom>
                Total Target Bonus
              </Typography>
              <Typography variant="h4">
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
                <BarChart
                  xAxis={[{
                    scaleType: 'band',
                    data: employeeData.map(emp => emp.name),
                  }]}
                  series={[{
                    data: employeeData.map(emp => parseFloat(emp.target_bonus)),
                    label: 'Target Bonus',
                  }]}
                  height={300}
                />
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
