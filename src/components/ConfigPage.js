import React from 'react';
import {
  Box,
  Paper,
  Typography,
  TextField,
  Button,
  Grid,
  Tab,
  Tabs,
  Divider,
  IconButton,
  List,
  ListItem,
  ListItemText,
  ListItemSecondaryAction,
  Dialog,
  DialogTitle,
  DialogContent,
  DialogActions,
  Alert,
  Snackbar,
  DialogContentText,
  Table,
  TableBody,
  TableCell,
  TableContainer,
  TableHead,
  TableRow,
  Card,
  CardContent,
} from '@mui/material';
import SaveIcon from '@mui/icons-material/Save';
import DeleteIcon from '@mui/icons-material/Delete';
import EditIcon from '@mui/icons-material/Edit';
import AddIcon from '@mui/icons-material/Add';
import ContentCopyIcon from '@mui/icons-material/ContentCopy';
import DownloadIcon from '@mui/icons-material/Download';
import UploadIcon from '@mui/icons-material/Upload';
import PreviewIcon from '@mui/icons-material/Preview';
import api from '../services/api';

function TabPanel({ children, value, index, ...other }) {
  return (
    <div
      role="tabpanel"
      hidden={value !== index}
      id={`config-tabpanel-${index}`}
      {...other}
    >
      {value === index && <Box sx={{ p: 3 }}>{children}</Box>}
    </div>
  );
}

function ConfigPage() {
  const [activeTab, setActiveTab] = React.useState(0);
  const [configs, setConfigs] = React.useState([]);
  const [selectedConfig, setSelectedConfig] = React.useState(null);
  const [openDialog, setOpenDialog] = React.useState(false);
  const [openConfirmDialog, setOpenConfirmDialog] = React.useState(false);
  const [openPreviewDialog, setOpenPreviewDialog] = React.useState(false);
  const [configToActivate, setConfigToActivate] = React.useState(null);
  const [formErrors, setFormErrors] = React.useState({});
  const [snackbar, setSnackbar] = React.useState({ open: false, message: '', severity: 'success' });
  const [previewData, setPreviewData] = React.useState([]);
  const [fileInput, setFileInput] = React.useState(null);
  const [configForm, setConfigForm] = React.useState({
    name: '',
    base_multiplier: '1.0',
    performance_weight: '0.4',
    revenue_weight: '0.6',
    min_bonus_percent: '0',
    max_bonus_percent: '200',
    description: '',
    is_active: false,
  });

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

  const fetchConfigs = async () => {
    try {
      const response = await api.get('/compensation-configs/');
      setConfigs(response.data);
    } catch (error) {
      console.error('Error fetching configs:', error);
      showSnackbar('Failed to load configurations', 'error');
    }
  };

  React.useEffect(() => {
    fetchConfigs();
  }, []);

  const handleTabChange = (event, newValue) => {
    setActiveTab(newValue);
  };

  const validateForm = () => {
    const errors = {};
    const performance = parseFloat(configForm.performance_weight);
    const revenue = parseFloat(configForm.revenue_weight);
    
    if (performance + revenue !== 1.0) {
      errors.weights = 'Performance weight and revenue weight must sum to 1.0';
    }

    if (!configForm.name.trim()) {
      errors.name = 'Name is required';
    }

    if (parseFloat(configForm.base_multiplier) <= 0) {
      errors.base_multiplier = 'Base multiplier must be greater than 0';
    }

    if (parseFloat(configForm.min_bonus_percent) < 0) {
      errors.min_bonus_percent = 'Minimum bonus percentage cannot be negative';
    }

    if (parseFloat(configForm.max_bonus_percent) <= parseFloat(configForm.min_bonus_percent)) {
      errors.max_bonus_percent = 'Maximum bonus percentage must be greater than minimum';
    }

    setFormErrors(errors);
    return Object.keys(errors).length === 0;
  };

  const handleSaveConfig = async () => {
    if (!validateForm()) {
      showSnackbar('Please correct the form errors', 'error');
      return;
    }

    try {
      if (selectedConfig) {
        await api.put(`/compensation-configs/${selectedConfig.id}/`, configForm);
        showSnackbar('Configuration updated successfully');
      } else {
        await api.post('/compensation-configs/', configForm);
        showSnackbar('Configuration created successfully');
      }
      fetchConfigs();
      handleCloseDialog();
    } catch (error) {
      console.error('Error saving config:', error);
      showSnackbar('Failed to save configuration', 'error');
    }
  };

  const handleSetActiveClick = (config) => {
    setConfigToActivate(config);
    setOpenConfirmDialog(true);
  };

  const handleSetActive = async () => {
    if (!configToActivate) return;

    try {
      await api.put(`/compensation-configs/${configToActivate.id}/`, {
        ...configToActivate,
        is_active: true
      });
      showSnackbar('Active configuration updated');
      fetchConfigs();
    } catch (error) {
      console.error('Error setting active config:', error);
      showSnackbar('Failed to update active configuration', 'error');
    } finally {
      setOpenConfirmDialog(false);
      setConfigToActivate(null);
    }
  };

  const handleDuplicateConfig = (config) => {
    const duplicatedConfig = {
      ...config,
      name: `${config.name} (Copy)`,
      is_active: false,
      id: undefined
    };
    setConfigForm(duplicatedConfig);
    setSelectedConfig(null);
    setOpenDialog(true);
  };

  const calculatePreview = (config) => {
    // Example employees for preview
    const sampleEmployees = [
      {
        name: "High Performer",
        base_salary: 100000,
        performance_score: 0.9,
        last_year_revenue: 1000000,
        pool_share: 0.1
      },
      {
        name: "Average Performer",
        base_salary: 100000,
        performance_score: 0.7,
        last_year_revenue: 800000,
        pool_share: 0.1
      },
      {
        name: "Low Performer",
        base_salary: 100000,
        performance_score: 0.5,
        last_year_revenue: 600000,
        pool_share: 0.1
      }
    ];

    const results = sampleEmployees.map(employee => {
      const performanceComponent = parseFloat(config.performance_weight) * employee.performance_score;
      const revenueComponent = parseFloat(config.revenue_weight) * (employee.last_year_revenue * employee.pool_share / employee.base_salary);
      const totalScore = (performanceComponent + revenueComponent) * parseFloat(config.base_multiplier);
      
      const bonusPercent = Math.min(
        Math.max(totalScore * 100, parseFloat(config.min_bonus_percent)),
        parseFloat(config.max_bonus_percent)
      );
      
      const bonusAmount = (employee.base_salary * bonusPercent) / 100;

      return {
        ...employee,
        performance_component: performanceComponent,
        revenue_component: revenueComponent,
        total_score: totalScore,
        bonus_percent: bonusPercent,
        bonus_amount: bonusAmount
      };
    });

    return results;
  };

  const handlePreviewConfig = (config) => {
    const results = calculatePreview(config);
    setPreviewData(results);
    setOpenPreviewDialog(true);
  };

  const handleExportConfigs = () => {
    const configsToExport = configs.map(({ id, created_at, updated_at, ...rest }) => rest);
    const blob = new Blob([JSON.stringify(configsToExport, null, 2)], { type: 'application/json' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = 'compensation-configs.json';
    document.body.appendChild(a);
    a.click();
    document.body.removeChild(a);
    URL.revokeObjectURL(url);
  };

  const handleImportConfigs = async (event) => {
    const file = event.target.files[0];
    if (!file) return;

    try {
      const reader = new FileReader();
      reader.onload = async (e) => {
        try {
          const configs = JSON.parse(e.target.result);
          for (const config of configs) {
            await api.post('/compensation-configs/', config);
          }
          showSnackbar('Configurations imported successfully');
          fetchConfigs();
        } catch (error) {
          console.error('Error importing configs:', error);
          showSnackbar('Failed to import configurations', 'error');
        }
      };
      reader.readAsText(file);
    } catch (error) {
      console.error('Error reading file:', error);
      showSnackbar('Failed to read import file', 'error');
    }
    // Reset file input
    if (fileInput) {
      fileInput.value = '';
    }
  };

  const handleInputChange = (e) => {
    const { name, value } = e.target;
    setConfigForm(prev => ({
      ...prev,
      [name]: value
    }));
    
    // Clear error for this field when user starts typing
    if (formErrors[name]) {
      setFormErrors(prev => ({
        ...prev,
        [name]: undefined
      }));
    }

    // Clear weights error if either weight is changed
    if (name === 'performance_weight' || name === 'revenue_weight') {
      setFormErrors(prev => ({
        ...prev,
        weights: undefined
      }));
    }
  };

  const handleOpenDialog = (config = null) => {
    if (config) {
      setConfigForm({
        ...config,
        base_multiplier: config.base_multiplier.toString(),
        performance_weight: config.performance_weight.toString(),
        revenue_weight: config.revenue_weight.toString(),
        min_bonus_percent: config.min_bonus_percent.toString(),
        max_bonus_percent: config.max_bonus_percent.toString(),
      });
      setSelectedConfig(config);
    } else {
      setConfigForm({
        name: '',
        base_multiplier: '1.0',
        performance_weight: '0.4',
        revenue_weight: '0.6',
        min_bonus_percent: '0',
        max_bonus_percent: '200',
        description: '',
        is_active: false,
      });
      setSelectedConfig(null);
    }
    setOpenDialog(true);
  };

  const handleCloseDialog = () => {
    setOpenDialog(false);
    setSelectedConfig(null);
  };

  const showSnackbar = (message, severity = 'success') => {
    setSnackbar({ open: true, message, severity });
  };

  const handleDeleteConfig = async (id) => {
    if (window.confirm('Are you sure you want to delete this configuration?')) {
      try {
        await api.delete(`/compensation-configs/${id}/`);
        showSnackbar('Configuration deleted successfully');
        fetchConfigs();
      } catch (error) {
        console.error('Error deleting config:', error);
        showSnackbar('Failed to delete configuration', 'error');
      }
    }
  };

  return (
    <Box>
      <Box sx={{ borderBottom: 1, borderColor: 'divider', mb: 3 }}>
        <Tabs value={activeTab} onChange={(e, newValue) => setActiveTab(newValue)}>
          <Tab label="Compensation Settings" />
          <Tab label="Saved Configurations" />
          <Tab label="Explanation" />
        </Tabs>
      </Box>

      <TabPanel value={activeTab} index={0}>
        <Grid container spacing={3}>
          <Grid item xs={12}>
            <Typography variant="h6" gutterBottom>
              Active Configuration
            </Typography>
            {configs.find(c => c.is_active) ? (
              <Box sx={{ mb: 2 }}>
                <Typography variant="subtitle1">
                  {configs.find(c => c.is_active).name}
                </Typography>
                <Typography variant="body2" color="textSecondary">
                  {configs.find(c => c.is_active).description}
                </Typography>
              </Box>
            ) : (
              <Alert severity="info" sx={{ mb: 2 }}>
                No active configuration set
              </Alert>
            )}
          </Grid>

          <Grid item xs={12} md={6}>
            <Paper sx={{ p: 2 }}>
              <Typography variant="h6" gutterBottom>
                Performance Settings
              </Typography>
              <Grid container spacing={2}>
                <Grid item xs={12}>
                  <TextField
                    fullWidth
                    label="Base Multiplier"
                    value={configForm.base_multiplier}
                    name="base_multiplier"
                    onChange={handleInputChange}
                    type="number"
                    inputProps={{ step: '0.1', min: '0' }}
                    error={!!formErrors.base_multiplier}
                    helperText={formErrors.base_multiplier}
                  />
                </Grid>
                <Grid item xs={12}>
                  <TextField
                    fullWidth
                    label="Performance Weight"
                    value={configForm.performance_weight}
                    name="performance_weight"
                    onChange={handleInputChange}
                    type="number"
                    inputProps={{ step: '0.1', min: '0', max: '1' }}
                    error={!!formErrors.performance_weight}
                    helperText={formErrors.performance_weight}
                  />
                </Grid>
              </Grid>
            </Paper>
          </Grid>

          <Grid item xs={12} md={6}>
            <Paper sx={{ p: 2 }}>
              <Typography variant="h6" gutterBottom>
                Bonus Settings
              </Typography>
              <Grid container spacing={2}>
                <Grid item xs={12}>
                  <TextField
                    fullWidth
                    label="Revenue Weight"
                    value={configForm.revenue_weight}
                    name="revenue_weight"
                    onChange={handleInputChange}
                    type="number"
                    inputProps={{ step: '0.1', min: '0', max: '1' }}
                    error={!!formErrors.revenue_weight}
                    helperText={formErrors.revenue_weight}
                  />
                </Grid>
                <Grid item xs={6}>
                  <TextField
                    fullWidth
                    label="Min Bonus %"
                    value={configForm.min_bonus_percent}
                    name="min_bonus_percent"
                    onChange={handleInputChange}
                    type="number"
                    inputProps={{ min: '0' }}
                    error={!!formErrors.min_bonus_percent}
                    helperText={formErrors.min_bonus_percent}
                  />
                </Grid>
                <Grid item xs={6}>
                  <TextField
                    fullWidth
                    label="Max Bonus %"
                    value={configForm.max_bonus_percent}
                    name="max_bonus_percent"
                    onChange={handleInputChange}
                    type="number"
                    inputProps={{ min: '0' }}
                    error={!!formErrors.max_bonus_percent}
                    helperText={formErrors.max_bonus_percent}
                  />
                </Grid>
              </Grid>
            </Paper>
          </Grid>

          <Grid item xs={12}>
            <Box sx={{ display: 'flex', justifyContent: 'flex-end', mt: 2 }}>
              <Button
                variant="contained"
                startIcon={<SaveIcon />}
                onClick={() => handleOpenDialog()}
              >
                Save as New Configuration
              </Button>
            </Box>
          </Grid>
        </Grid>
      </TabPanel>

      <TabPanel value={activeTab} index={1}>
        <Box sx={{ mb: 2, display: 'flex', gap: 2 }}>
          <Button
            variant="contained"
            startIcon={<AddIcon />}
            onClick={() => handleOpenDialog()}
          >
            Add New Configuration
          </Button>
          <Button
            variant="outlined"
            startIcon={<DownloadIcon />}
            onClick={handleExportConfigs}
          >
            Export Configs
          </Button>
          <Button
            variant="outlined"
            startIcon={<UploadIcon />}
            component="label"
          >
            Import Configs
            <input
              type="file"
              hidden
              accept=".json"
              onChange={handleImportConfigs}
              ref={input => setFileInput(input)}
            />
          </Button>
        </Box>
        <List>
          {configs.map((config) => (
            <React.Fragment key={config.id}>
              <ListItem>
                <ListItemText
                  primary={
                    <Typography variant="subtitle1">
                      {config.name} {config.is_active && <em>(Active)</em>}
                    </Typography>
                  }
                  secondary={
                    <>
                      <Typography component="span" variant="body2" color="text.primary">
                        Base Multiplier: {config.base_multiplier} | Performance: {config.performance_weight * 100}% | Revenue: {config.revenue_weight * 100}%
                      </Typography>
                      <br />
                      <Typography variant="body2" color="text.secondary">
                        {config.description}
                      </Typography>
                    </>
                  }
                />
                <ListItemSecondaryAction>
                  <Button
                    variant="outlined"
                    size="small"
                    onClick={() => handlePreviewConfig(config)}
                    sx={{ mr: 1 }}
                    startIcon={<PreviewIcon />}
                  >
                    Preview
                  </Button>
                  {!config.is_active && (
                    <Button
                      variant="outlined"
                      size="small"
                      onClick={() => handleSetActiveClick(config)}
                      sx={{ mr: 1 }}
                    >
                      Set Active
                    </Button>
                  )}
                  <IconButton
                    onClick={() => handleDuplicateConfig(config)}
                    sx={{ mr: 1 }}
                  >
                    <ContentCopyIcon />
                  </IconButton>
                  <IconButton
                    onClick={() => handleOpenDialog(config)}
                    sx={{ mr: 1 }}
                  >
                    <EditIcon />
                  </IconButton>
                  <IconButton
                    onClick={() => handleDeleteConfig(config.id)}
                  >
                    <DeleteIcon />
                  </IconButton>
                </ListItemSecondaryAction>
              </ListItem>
              <Divider />
            </React.Fragment>
          ))}
        </List>
      </TabPanel>

      <TabPanel value={activeTab} index={2}>
        <Box sx={{ p: 3 }}>
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
      </TabPanel>

      <Dialog open={openDialog} onClose={handleCloseDialog} maxWidth="sm" fullWidth>
        <DialogTitle>
          {selectedConfig ? 'Edit Configuration' : 'New Configuration'}
        </DialogTitle>
        <DialogContent>
          {formErrors.weights && (
            <Alert severity="error" sx={{ mt: 2, mb: 2 }}>
              {formErrors.weights}
            </Alert>
          )}
          <Grid container spacing={2} sx={{ mt: 1 }}>
            <Grid item xs={12}>
              <TextField
                fullWidth
                label="Configuration Name"
                name="name"
                value={configForm.name}
                onChange={handleInputChange}
                error={!!formErrors.name}
                helperText={formErrors.name}
                required
              />
            </Grid>
            <Grid item xs={12}>
              <TextField
                fullWidth
                label="Description"
                name="description"
                value={configForm.description}
                onChange={handleInputChange}
                multiline
                rows={3}
              />
            </Grid>
            <Grid item xs={12} sm={6}>
              <TextField
                fullWidth
                label="Base Multiplier"
                name="base_multiplier"
                value={configForm.base_multiplier}
                onChange={handleInputChange}
                type="number"
                inputProps={{ step: '0.1', min: '0' }}
                error={!!formErrors.base_multiplier}
                helperText={formErrors.base_multiplier}
              />
            </Grid>
            <Grid item xs={12} sm={6}>
              <TextField
                fullWidth
                label="Performance Weight"
                name="performance_weight"
                value={configForm.performance_weight}
                onChange={handleInputChange}
                type="number"
                inputProps={{ step: '0.1', min: '0', max: '1' }}
                error={!!formErrors.performance_weight}
                helperText={formErrors.performance_weight}
              />
            </Grid>
            <Grid item xs={12} sm={6}>
              <TextField
                fullWidth
                label="Revenue Weight"
                name="revenue_weight"
                value={configForm.revenue_weight}
                onChange={handleInputChange}
                type="number"
                inputProps={{ step: '0.1', min: '0', max: '1' }}
                error={!!formErrors.revenue_weight}
                helperText={formErrors.revenue_weight}
              />
            </Grid>
            <Grid item xs={12} sm={6}>
              <TextField
                fullWidth
                label="Min Bonus %"
                name="min_bonus_percent"
                value={configForm.min_bonus_percent}
                onChange={handleInputChange}
                type="number"
                inputProps={{ min: '0' }}
                error={!!formErrors.min_bonus_percent}
                helperText={formErrors.min_bonus_percent}
              />
            </Grid>
            <Grid item xs={12} sm={6}>
              <TextField
                fullWidth
                label="Max Bonus %"
                name="max_bonus_percent"
                value={configForm.max_bonus_percent}
                onChange={handleInputChange}
                type="number"
                inputProps={{ min: '0' }}
                error={!!formErrors.max_bonus_percent}
                helperText={formErrors.max_bonus_percent}
              />
            </Grid>
          </Grid>
        </DialogContent>
        <DialogActions>
          <Button onClick={handleCloseDialog}>Cancel</Button>
          <Button onClick={handleSaveConfig} variant="contained">
            {selectedConfig ? 'Save Changes' : 'Create Configuration'}
          </Button>
        </DialogActions>
      </Dialog>

      <Dialog
        open={openConfirmDialog}
        onClose={() => setOpenConfirmDialog(false)}
        aria-labelledby="confirm-dialog-title"
      >
        <DialogTitle id="confirm-dialog-title">
          Set Active Configuration
        </DialogTitle>
        <DialogContent>
          <DialogContentText>
            Are you sure you want to set "{configToActivate?.name}" as the active configuration?
            This will deactivate the current active configuration.
          </DialogContentText>
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setOpenConfirmDialog(false)}>Cancel</Button>
          <Button onClick={handleSetActive} variant="contained" color="primary">
            Confirm
          </Button>
        </DialogActions>
      </Dialog>

      <Dialog
        open={openPreviewDialog}
        onClose={() => setOpenPreviewDialog(false)}
        maxWidth="md"
        fullWidth
      >
        <DialogTitle>
          Preview Calculation Results
        </DialogTitle>
        <DialogContent>
          <Typography variant="body2" color="text.secondary" sx={{ mb: 2 }}>
            This preview shows how the configuration would affect different types of employees.
            The calculation uses sample data for illustration purposes.
          </Typography>
          <TableContainer component={Paper}>
            <Table size="small">
              <TableHead>
                <TableRow>
                  <TableCell>Employee</TableCell>
                  <TableCell align="right">Base Salary</TableCell>
                  <TableCell align="right">Performance Score</TableCell>
                  <TableCell align="right">Revenue</TableCell>
                  <TableCell align="right">Performance Component</TableCell>
                  <TableCell align="right">Revenue Component</TableCell>
                  <TableCell align="right">Bonus %</TableCell>
                  <TableCell align="right">Bonus Amount</TableCell>
                </TableRow>
              </TableHead>
              <TableBody>
                {previewData.map((row) => (
                  <TableRow key={row.name}>
                    <TableCell>{row.name}</TableCell>
                    <TableCell align="right">${row.base_salary.toLocaleString()}</TableCell>
                    <TableCell align="right">{(row.performance_score * 100).toFixed(1)}%</TableCell>
                    <TableCell align="right">${row.last_year_revenue.toLocaleString()}</TableCell>
                    <TableCell align="right">{(row.performance_component * 100).toFixed(1)}%</TableCell>
                    <TableCell align="right">{(row.revenue_component * 100).toFixed(1)}%</TableCell>
                    <TableCell align="right">{row.bonus_percent.toFixed(1)}%</TableCell>
                    <TableCell align="right">${row.bonus_amount.toLocaleString()}</TableCell>
                  </TableRow>
                ))}
              </TableBody>
            </Table>
          </TableContainer>
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setOpenPreviewDialog(false)}>Close</Button>
        </DialogActions>
      </Dialog>

      <Snackbar
        open={snackbar.open}
        autoHideDuration={6000}
        onClose={() => setSnackbar({ ...snackbar, open: false })}
      >
        <Alert
          onClose={() => setSnackbar({ ...snackbar, open: false })}
          severity={snackbar.severity}
        >
          {snackbar.message}
        </Alert>
      </Snackbar>
    </Box>
  );
}

export default ConfigPage;
