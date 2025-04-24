import React from 'react';
import {
  Box,
  Paper,
  Typography,
  Button,
  Table,
  TableBody,
  TableCell,
  TableContainer,
  TableHead,
  TableRow,
  IconButton,
  Dialog,
  DialogTitle,
  DialogContent,
  DialogActions,
  TextField,
} from '@mui/material';
import AddIcon from '@mui/icons-material/Add';
import EditIcon from '@mui/icons-material/Edit';
import DeleteIcon from '@mui/icons-material/Delete';
import CsvUpload from './CsvUpload';
import api from '../services/api';

function EmployeeManagement() {
  const [employees, setEmployees] = React.useState([]);
  const [openDialog, setOpenDialog] = React.useState(false);
  const [selectedEmployee, setSelectedEmployee] = React.useState(null);
  const [formData, setFormData] = React.useState({
    name: '',
    base_salary: '',
    pool_share: '',
    target_bonus: '',
    performance_score: '',
    last_year_revenue: '',
  });

  const fetchEmployees = async () => {
    try {
      const response = await api.get('/employees/');
      setEmployees(response.data);
    } catch (error) {
      console.error('Error fetching employees:', error);
    }
  };

  React.useEffect(() => {
    fetchEmployees();
  }, []);

  const handleOpenDialog = (employee = null) => {
    if (employee) {
      setFormData(employee);
      setSelectedEmployee(employee);
    } else {
      setFormData({
        name: '',
        base_salary: '',
        pool_share: '',
        target_bonus: '',
        performance_score: '',
        last_year_revenue: '',
      });
      setSelectedEmployee(null);
    }
    setOpenDialog(true);
  };

  const handleCloseDialog = () => {
    setOpenDialog(false);
    setSelectedEmployee(null);
    setFormData({
      name: '',
      base_salary: '',
      pool_share: '',
      target_bonus: '',
      performance_score: '',
      last_year_revenue: '',
    });
  };

  const handleInputChange = (e) => {
    const { name, value } = e.target;
    setFormData(prev => ({
      ...prev,
      [name]: value
    }));
  };

  const handleSubmit = async () => {
    try {
      if (selectedEmployee) {
        await api.put(`/employees/${selectedEmployee.id}/`, formData);
      } else {
        await api.post('/employees/', formData);
      }
      fetchEmployees();
      handleCloseDialog();
    } catch (error) {
      console.error('Error saving employee:', error);
    }
  };

  const handleDelete = async (id) => {
    if (window.confirm('Are you sure you want to delete this employee?')) {
      try {
        await api.delete(`/employees/${id}/`);
        fetchEmployees();
      } catch (error) {
        console.error('Error deleting employee:', error);
      }
    }
  };

  return (
    <Box>
      <Box sx={{ display: 'flex', justifyContent: 'space-between', mb: 3 }}>
        <Typography variant="h4" component="h1">
          Employee Management
        </Typography>
        <Button
          variant="contained"
          startIcon={<AddIcon />}
          onClick={() => handleOpenDialog()}
        >
          Add Employee
        </Button>
      </Box>

      <CsvUpload onUploadSuccess={fetchEmployees} />

      <TableContainer component={Paper} sx={{ mt: 3 }}>
        <Table>
          <TableHead>
            <TableRow>
              <TableCell>Name</TableCell>
              <TableCell align="right">Base Salary</TableCell>
              <TableCell align="right">Pool Share</TableCell>
              <TableCell align="right">Target Bonus</TableCell>
              <TableCell align="right">Performance Score</TableCell>
              <TableCell align="right">Last Year Revenue</TableCell>
              <TableCell align="center">Actions</TableCell>
            </TableRow>
          </TableHead>
          <TableBody>
            {employees.map((employee) => (
              <TableRow key={employee.id}>
                <TableCell>{employee.name}</TableCell>
                <TableCell align="right">${employee.base_salary}</TableCell>
                <TableCell align="right">{(employee.pool_share * 100).toFixed(2)}%</TableCell>
                <TableCell align="right">${employee.target_bonus}</TableCell>
                <TableCell align="right">{(employee.performance_score * 100).toFixed(2)}%</TableCell>
                <TableCell align="right">${employee.last_year_revenue}</TableCell>
                <TableCell align="center">
                  <IconButton onClick={() => handleOpenDialog(employee)}>
                    <EditIcon />
                  </IconButton>
                  <IconButton onClick={() => handleDelete(employee.id)}>
                    <DeleteIcon />
                  </IconButton>
                </TableCell>
              </TableRow>
            ))}
          </TableBody>
        </Table>
      </TableContainer>

      <Dialog open={openDialog} onClose={handleCloseDialog} maxWidth="sm" fullWidth>
        <DialogTitle>
          {selectedEmployee ? 'Edit Employee' : 'Add Employee'}
        </DialogTitle>
        <DialogContent>
          <Box sx={{ display: 'flex', flexDirection: 'column', gap: 2, mt: 2 }}>
            <TextField
              name="name"
              label="Name"
              value={formData.name}
              onChange={handleInputChange}
              fullWidth
            />
            <TextField
              name="base_salary"
              label="Base Salary"
              type="number"
              value={formData.base_salary}
              onChange={handleInputChange}
              fullWidth
            />
            <TextField
              name="pool_share"
              label="Pool Share (%)"
              type="number"
              value={formData.pool_share}
              onChange={handleInputChange}
              fullWidth
              inputProps={{ step: '0.01', min: '0', max: '100' }}
            />
            <TextField
              name="target_bonus"
              label="Target Bonus"
              type="number"
              value={formData.target_bonus}
              onChange={handleInputChange}
              fullWidth
            />
            <TextField
              name="performance_score"
              label="Performance Score (%)"
              type="number"
              value={formData.performance_score}
              onChange={handleInputChange}
              fullWidth
              inputProps={{ step: '0.01', min: '0', max: '100' }}
            />
            <TextField
              name="last_year_revenue"
              label="Last Year Revenue"
              type="number"
              value={formData.last_year_revenue}
              onChange={handleInputChange}
              fullWidth
            />
          </Box>
        </DialogContent>
        <DialogActions>
          <Button onClick={handleCloseDialog}>Cancel</Button>
          <Button onClick={handleSubmit} variant="contained">
            {selectedEmployee ? 'Save' : 'Add'}
          </Button>
        </DialogActions>
      </Dialog>
    </Box>
  );
}

export default EmployeeManagement;
