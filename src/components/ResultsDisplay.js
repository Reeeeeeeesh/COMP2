import React from 'react';
import { 
  TableContainer, 
  Paper, 
  Table, 
  TableHead, 
  TableRow, 
  TableCell, 
  TableBody, 
  Typography, 
  Box,
  Chip
} from '@mui/material';

const ResultsDisplay = ({ results, summary }) => {
  // Detect if we're displaying proposed model results
  const isProposedModel = results.length > 0 && 'new_salary' in results[0];

  return (
    <Box mt={4}>
      <Typography variant="h6" gutterBottom>Results</Typography>
      {isProposedModel ? (
        // Proposed Model Results
        <>
          <TableContainer component={Paper} sx={{ mb: 2 }}>
            <Table size="small">
              <TableHead>
                <TableRow>
                  <TableCell>Employee</TableCell>
                  <TableCell>Team</TableCell>
                  <TableCell align="right">Original Salary</TableCell>
                  <TableCell align="right">New Salary</TableCell>
                  <TableCell align="right">Increase</TableCell>
                  <TableCell align="right">Performance</TableCell>
                  <TableCell align="right">Revenue Trend</TableCell>
                  <TableCell align="right">Bonus</TableCell>
                  <TableCell align="right">Total Comp</TableCell>
                  <TableCell align="right">Regulatory</TableCell>
                </TableRow>
              </TableHead>
              <TableBody>
                {results.map((row, index) => {
                  console.log(`Rendering Row ${index}:`, row.employee, 'Rating:', row.performance_rating);
                  return (
                    <TableRow key={row.employee}>
                      <TableCell>{row.employee}</TableCell>
                      <TableCell>{row.team || '-'}</TableCell>
                      <TableCell align="right">{row.original_salary}</TableCell>
                      <TableCell align="right">{row.new_salary}</TableCell>
                      <TableCell align="right">{row.salary_increase}</TableCell>
                      <TableCell align="right">{row.performance_rating}</TableCell>
                      <TableCell align="right">{row.team_revenue_trend}</TableCell>
                      <TableCell align="right">{row.bonus_amount}</TableCell>
                      <TableCell align="right">{row.total_compensation}</TableCell>
                      <TableCell align="right">
                        {row.deferral_applied && 
                          <Chip 
                            size="small" 
                            color="primary" 
                            label="Deferral" 
                            title={`Deferred: ${row.deferred_amount}`}
                          />
                        }
                        {row.ratio_alert && 
                          <Chip 
                            size="small" 
                            color="error" 
                            label="Ratio" 
                            sx={{ ml: 0.5 }}
                            title="Variable:Fixed ratio exceeds threshold"
                          />
                        }
                      </TableCell>
                    </TableRow>
                  );
                })}
              </TableBody>
            </Table>
          </TableContainer>
          <Box display="flex" justifyContent="space-between">
            <Typography variant="subtitle1">
              Total Compensation: {summary.total_compensation}
            </Typography>
            <Typography variant="subtitle1">
              Employees: {summary.employee_count}
            </Typography>
          </Box>
        </>
      ) : (
        // Original Model Results
        <>
          <TableContainer component={Paper} sx={{ mb: 2 }}>
            <Table size="small">
              <TableHead>
                <TableRow>
                  <TableCell>Employee</TableCell>
                  <TableCell align="right">Original Base</TableCell>
                  <TableCell align="right">Adjusted Base</TableCell>
                  <TableCell align="right">Variable Portion</TableCell>
                  <TableCell align="right">Bonus</TableCell>
                  <TableCell align="right">Model A Total</TableCell>
                  <TableCell align="right">Model B Total</TableCell>
                  <TableCell align="right">Difference</TableCell>
                </TableRow>
              </TableHead>
              <TableBody>
                {results.map((row) => (
                  <TableRow key={row.employee}>
                    <TableCell>{row.employee}</TableCell>
                    <TableCell align="right">{row.original_base}</TableCell>
                    <TableCell align="right">{row.adjusted_base}</TableCell>
                    <TableCell align="right">{row.variable_portion}</TableCell>
                    <TableCell align="right">{row.bonus}</TableCell>
                    <TableCell align="right">{row.model_a_total}</TableCell>
                    <TableCell align="right">{row.model_b_total}</TableCell>
                    <TableCell align="right">{row.difference}</TableCell>
                  </TableRow>
                ))}
              </TableBody>
            </Table>
          </TableContainer>
          <Box display="flex" justifyContent="space-between">
            <Typography variant="subtitle1">
              Total Model A: {summary.total_model_a}
            </Typography>
            <Typography variant="subtitle1">
              Total Model B: {summary.total_model_b}
            </Typography>
          </Box>
        </>
      )}
    </Box>
  );
};

export default ResultsDisplay;
