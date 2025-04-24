import React from 'react';
import { BrowserRouter as Router, Routes, Route, Link, Navigate } from 'react-router-dom';
import { Box, Drawer, List, ListItem, ListItemIcon, ListItemText, Typography, CssBaseline, Paper } from '@mui/material';
import DashboardIcon from '@mui/icons-material/Dashboard';
import PeopleIcon from '@mui/icons-material/People';
import SettingsIcon from '@mui/icons-material/Settings';
import InfoIcon from '@mui/icons-material/Info';
import Dashboard from './components/Dashboard';
import EmployeeManagement from './components/EmployeeManagement';
import ConfigPage from './components/ConfigPage';
import api from './services/api';
import './App.css';

function App() {
  React.useEffect(() => {
    api.get('/ping/')
      .then(({ data }) => console.log('Ping:', data))
      .catch(err => console.error(err));
  }, []);

  const drawerWidth = 240;

  const explanationText = `1. Introduction: What is this Tool?
This tool is a sophisticated system designed to help businesses calculate, simulate, and compare different employee compensation scenarios. It allows you to:
•	Upload employee data easily.
•	Run calculations based on different compensation models.
•	Adjust key business parameters (like revenue changes) to see their impact.
•	Incorporate complex factors like performance ratings, job levels, market salary benchmarks (compa-ratio), and team performance.
•	Apply regulatory rules, particularly for employees identified as Material Risk Takers (MRTs).
•	Compare the outcomes of different compensation approaches.
Essentially, it helps you make informed decisions about salary adjustments and bonus payouts by modeling potential outcomes based on your data and defined rules.

2. Core Concepts You Need to Know
The tool uses several key concepts and models:
•	Model A (Base Salary Adjustment): This is a simpler model focused only on adjusting an employee's base salary. 
o	How it works: It takes the employee's current base_salary and adjusts it based on two main inputs you provide: 
	revenue_delta: The percentage change (positive or negative) in overall revenue you want to simulate.
	adjustment_factor: A multiplier determining how strongly the revenue_delta impacts the salary change.
o	Guardrails: To prevent extreme changes, adjustments are capped at a maximum increase (e.g., +20%) and floored at a maximum decrease (e.g., -10%) relative to the original base salary.
•	Model B (Bonus Calculation): This model focuses only on calculating a bonus amount, separate from the base salary. It has two distinct methods you can choose between: 
o	Pool Method: Calculates the bonus based on a share of revenue. 
	How it works: Bonus = Employee's pool_share × (Last Year's Revenue × (1 + revenue_delta)). The revenue_delta you provide adjusts the revenue figure used.
o	Target Method: Calculates the bonus based on achieving a target amount, adjusted by performance. 
	How it works: Bonus = Employee's target_bonus × Employee's performance_score. The performance_score is capped at 1.0 (or 100%) for this calculation, meaning performance above 100% doesn't increase the bonus beyond the target amount.
•	The "Proposed Model" (Integrated Merit & Bonus): This is the most advanced model, integrating salary increases (merit) and bonus calculations based on multiple factors. It aims to provide a more holistic compensation picture. 
o	Merit Increase (Salary Adjustment): 
	How it works: The percentage increase applied to the base_salary is determined by: 
	Performance Rating: Categorical rating (e.g., 'Exceeds Expectations', 'Meets Expectations').
	Compa-Ratio Quartile: Where the employee's salary sits relative to the market midpoint for their specific role and level (requires Salary Band configuration). The tool calculates this ratio and determines if it falls into Quartile 1 (lowest) to Quartile 4 (highest).
	Team Revenue Trend: Looks at the historical revenue performance (e.g., last 3 years) of the employee's assigned Team (requires Team and Team Revenue configuration) and categorizes it (e.g., 'Strong Growth', 'Stable', 'Decline').
	Merit Matrix: A configurable table that defines a base merit increase percentage based on the Performance Rating and Compa-Ratio Quartile.
	Revenue Trend Factor: A configurable multiplier that adjusts the base merit increase based on the Team Revenue Trend.
o	Bonus Calculation: 
	How it works: Bonus = Employee's target_bonus × KPI Achievement. 
	KPI Achievement: Ideally, this uses specific Key Performance Indicator (KPI) achievement data loaded for the employee for the relevant year (requires KPI Achievement configuration). KPIs might include weighted scores for investment performance, risk management, revenue generation (AUM), and qualitative factors.
	Fallback: If specific KPI data isn't available for an employee, the tool uses their performance_rating (converted to a score) or their raw performance_score as a fallback to calculate the achievement multiplier.
•	Material Risk Taker (MRT): This is a flag (is_mrt) you set for each employee. If an employee is marked as an MRT (TRUE), specific regulatory rules automatically apply to their calculated bonus (if it exceeds certain thresholds): 
o	Deferral: A portion of the bonus (e.g., 40%) must be deferred over time if the total bonus exceeds a threshold (e.g., £500k).
o	Instrument Split: The deferred portion is often required to be split between cash and other instruments (like stock, e.g., 50%/50%).
o	Ratio Alert: The tool flags if the variable pay (bonus) exceeds a certain ratio of the fixed pay (base salary), e.g., 1:1.
•	Configuration Data: The sophisticated "Proposed Model" relies heavily on background data that defines the rules: 
o	Teams: List of teams employees can belong to.
o	Salary Bands: Defines Min, Mid, and Max salary values for each Role and Level combination. Used to calculate compa-ratios.
o	Team Revenues: Historical annual revenue figures for each Team. Used to calculate revenue trends.
o	Merit Matrix: Defines the base merit increase percentages based on performance and compa-ratio position.
o	Revenue Trend Factors: Defines the multipliers applied to merit increases based on team revenue trends.
o	KPI Achievements: Records specific, weighted KPI scores for employees per year.

3. How to Use the Tool: Step-by-Step
1.	Prepare Your Data:
o	Employee Data: You need a CSV file containing your employee information. 
	Required Columns (for basic Model A/B): name, base_salary, pool_share, target_bonus, performance_score, last_year_revenue.
	Required/Recommended Columns (for Proposed Model): Add role, level, is_mrt (use TRUE or FALSE), performance_rating (e.g., Exceeds Expectations). Ensure the performance_rating text matches the values defined in your Merit Matrix configuration exactly.
	You can see examples in sample_data_enhanced.csv and sample_data_with_ratings.csv.
o	Configuration Data (for Proposed Model): Prepare CSV files for Teams, Salary Bands, Team Revenues, Merit Matrix, Revenue Trend Factors, and KPI Achievements based on the structures defined in the system. There's also a bulk upload option requiring a single CSV file with specific formatting (sections separated by blank lines, specific headers per section).

2.	Upload Data:
o	Employee Data: Use the tool's interface (likely via the /api/upload-data/ endpoint) to upload your main employee CSV file. The system will try to match employees by name to update existing records or create new ones. Pay attention to any reported errors during upload.
o	Configuration Data: Use the dedicated upload interfaces (e.g., /api/teams/upload/, /api/salary-bands/upload/, or the /api/config-bulk-upload/ endpoint) to load your configuration rules. Note: The bulk upload typically clears existing configuration data first, making your file the new source of truth.

3.	Run Calculations:
o	Navigate to the calculation/scenario section of the tool (interacting with the /api/calculate/ endpoint).
o	Choose the Model: Select whether you want to run the simple "Model A vs Model B" comparison or the advanced "Proposed Model".
o	Set Parameters: 
	If running Model A/B: 
	Enter the revenue_delta (e.g., 0.1 for +10%, -0.05 for -5%).
	Enter the adjustment_factor for Model A (e.g., 1).
	Choose whether Model B should use the Pool Method or the Target Method.
	If running the Proposed Model: 
	Enter the current_year for which the calculation applies (used for fetching relevant KPI/Revenue data).
	Decide if you want to Use Overrides. 
	If YES: Select a single performance_rating and is_mrt status (TRUE/FALSE) that will be applied to all employees for this specific calculation run, ignoring their individual data for these fields.
	If NO: The calculation will use the performance_rating and is_mrt status uploaded individually for each employee. (Important: If running without overrides, only employees who had a valid performance_rating in the uploaded CSV will be included in the calculation results).
o	Execute: Trigger the calculation.

4.	Review Results:
o	The tool will display the results, likely in a table format.
o	Model A/B Output: You'll see columns for each employee showing their original base, the calculated adjusted base (Model A), the calculated bonus (Model B - Pool or Target), the total compensation under each model, and the difference between them. A summary showing the total cost for each model across all employees is also provided.
o	Proposed Model Output: You'll see columns for each employee showing their original salary, the calculated new salary (after merit increase), the salary increase amount, the bonus amount, the total compensation, and a breakdown of the bonus into immediate cash, deferred cash, and deferred instruments (if applicable based on MRT status and thresholds). Flags for deferral_applied and ratio_alert will also be shown. A summary provides the total compensation cost and employee count.

5. Iterate: Adjust the input parameters (revenue delta, model choices, overrides) and re-run the calculations to explore different scenarios and understand their impact on individual compensation and overall cost.

In Summary:
This tool acts as a powerful compensation calculator and simulator. You feed it employee data and configuration rules (either basic or complex). You then select a calculation model (simple base/bonus comparison OR integrated merit/bonus/regulatory) and set scenario parameters. The tool processes the data according to the chosen model and rules, applies caps/floors and regulatory constraints where needed, and presents detailed results for each employee and overall totals, allowing you to compare outcomes and make data-driven compensation decisions.`;

  return (
    <Router>
      <Box sx={{ display: 'flex' }}>
        <CssBaseline />
        <Drawer
          variant="permanent"
          sx={{
            width: drawerWidth,
            flexShrink: 0,
            '& .MuiDrawer-paper': {
              width: drawerWidth,
              boxSizing: 'border-box',
              backgroundColor: '#1a1a1a',
              color: 'white',
            },
          }}
        >
          <Box sx={{ overflow: 'auto', mt: 2 }}>
            <List>
              <ListItem button component={Link} to="/">
                <ListItemIcon sx={{ color: 'white' }}>
                  <DashboardIcon />
                </ListItemIcon>
                <ListItemText primary="Dashboard" />
              </ListItem>
              <ListItem button component={Link} to="/employees">
                <ListItemIcon sx={{ color: 'white' }}>
                  <PeopleIcon />
                </ListItemIcon>
                <ListItemText primary="Employee Management" />
              </ListItem>
              <ListItem button component={Link} to="/config">
                <ListItemIcon sx={{ color: 'white' }}>
                  <SettingsIcon />
                </ListItemIcon>
                <ListItemText primary="Configuration" />
              </ListItem>
              <ListItem button component={Link} to="/explanation">
                <ListItemIcon sx={{ color: 'white' }}>
                  <InfoIcon />
                </ListItemIcon>
                <ListItemText primary="Explanation" />
              </ListItem>
            </List>
          </Box>
        </Drawer>
        <Box component="main" sx={{ flexGrow: 1, p: 3 }}>
          <Routes>
            <Route path="/" element={<Dashboard />} />
            <Route path="/employees" element={<EmployeeManagement />} />
            <Route path="/config" element={<ConfigPage />} />
            <Route path="/explanation" element={
              <Box sx={{ p: 3 }}>
                <Typography variant="h4" component="h1" gutterBottom>
                  Fund Manager Compensation Tool Guide
                </Typography>
                <Paper sx={{ p: 3, maxWidth: '100%', overflowX: 'auto' }}>
                  <Typography
                    component="pre"
                    sx={{
                      whiteSpace: 'pre-wrap',
                      fontFamily: 'inherit',
                      fontSize: '1rem',
                      lineHeight: 1.6
                    }}
                  >
                    {explanationText}
                  </Typography>
                </Paper>
              </Box>
            } />
            <Route path="*" element={<Navigate to="/" replace />} />
          </Routes>
        </Box>
      </Box>
    </Router>
  );
}

export default App;
