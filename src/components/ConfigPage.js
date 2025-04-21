import React, { useEffect, useState } from 'react';
import { 
  Box, Typography, Tabs, Tab, Button, TableContainer, Paper, Table, TableHead, TableBody, TableRow, TableCell,
  Dialog, DialogTitle, DialogContent, DialogActions, TextField
} from '@mui/material';
import api from '../services/api';

function ConfigPage() {
  const [tab, setTab] = useState(0);
  const [salaryBands, setSalaryBands] = useState([]);
  const [teamRevenues, setTeamRevenues] = useState([]);
  const [meritMatrices, setMeritMatrices] = useState([]);
  const [revenueTrendFactors, setRevenueTrendFactors] = useState([]);
  const [kpiAchievements, setKpiAchievements] = useState([]);
  const [open, setOpen] = useState(false);
  const [model, setModel] = useState('');
  const [form, setForm] = useState({});
  const [uploadFile, setUploadFile] = useState(null);
  const [bulkFile, setBulkFile] = useState(null);
  const [bulkError, setBulkError] = useState('');
  const [teamFile, setTeamFile] = useState(null);

  useEffect(() => { fetchAll(); }, []);

  const fetchAll = async () => {
    const [sb, tr, mm, rtf, kpi] = await Promise.all([
      api.get('/salary-bands/'),
      api.get('/team-revenues/'),
      api.get('/merit-matrices/'),
      api.get('/revenue-trend-factors/'),
      api.get('/kpi-achievements/')
    ]);
    setSalaryBands(sb.data);
    setTeamRevenues(tr.data);
    setMeritMatrices(mm.data);
    setRevenueTrendFactors(rtf.data);
    setKpiAchievements(kpi.data);
  };

  const handleOpen = (modelName, item={}) => {
    setModel(modelName);
    setForm(item);
    setOpen(true);
  };
  const handleClose = () => setOpen(false);
  const handleSave = async () => {
    const endpoint = model.replace(/([A-Z])/g, '-$1').toLowerCase().slice(1);
    if (form.id) await api.put(`/${endpoint}/${form.id}/`, form);
    else await api.post(`/${endpoint}/`, form);
    handleClose(); fetchAll();
  };
  const handleDelete = async (item) => {
    const endpoint = model.replace(/([A-Z])/g, '-$1').toLowerCase().slice(1);
    await api.delete(`/${endpoint}/${item.id}/`);
    fetchAll();
  };

  const handleUpload = async () => {
    if (!uploadFile) {
      alert('Please select a CSV file first');
      return;
    }
    const endpointMap = {
      0: '/salary-bands/upload/',
      1: '/team-revenues/upload/',
      2: '/merit-matrices/upload/',
      3: '/revenue-trend-factors/upload/',
      4: '/kpi-achievements/upload/'
    };
    const url = endpointMap[tab];
    const formData = new FormData();
    formData.append('file', uploadFile);
    try {
      await api.post(url, formData, { headers: { 'Content-Type': 'multipart/form-data' } });
      setUploadFile(null);
      fetchAll();
      alert('Upload successful');
    } catch (err) {
      console.error(err);
      alert('Upload failed');
    }
  };

  const handleBulkUpload = async () => {
    if (!bulkFile) { alert('Please select a CSV file for bulk upload'); return; }
    const formData = new FormData();
    formData.append('file', bulkFile);
    try {
      await api.post('/config-bulk-upload/', formData, { headers: { 'Content-Type': 'multipart/form-data' } });
      setBulkFile(null);
      setBulkError('');
      fetchAll();
      alert('Bulk upload successful');
    } catch (err) {
      console.error(err);
      const detail = err.response && err.response.data ? JSON.stringify(err.response.data, null, 2) : err.message;
      setBulkError(detail);
      alert(`Bulk upload failed: ${detail}`);
    }
  };

  const handleTeamUpload = async () => {
    if (!teamFile) { alert('Select a Teams CSV first'); return; }
    const formData = new FormData();
    formData.append('file', teamFile);
    try {
      await api.post('/teams/upload/', formData, { headers: { 'Content-Type': 'multipart/form-data' } });
      setTeamFile(null);
      alert('Teams uploaded successfully');
    } catch (err) {
      const detail = err.response?.data ? JSON.stringify(err.response.data, null, 2) : err.message;
      alert(`Team upload failed: ${detail}`);
    }
  };

  const renderFields = () => {
    const fields = {
      SalaryBand: ['role','level','min_value','mid_value','max_value'],
      TeamRevenue: ['team','year','revenue'],
      MeritMatrix: ['performance_rating','compa_ratio_range','increase_percentage'],
      RevenueTrendFactor: ['trend_category','adjustment_factor'],
      KpiAchievement: ['employee','year','investment_performance','risk_management','aum_revenue','qualitative']
    };
    return fields[model]?.map(field => (
      <TextField key={field}
        label={field}
        fullWidth
        margin="dense"
        value={form[field] ?? ''}
        onChange={e => setForm({ ...form, [field]: e.target.value })}
      />
    ));
  };

  const renderTable = () => {
    switch(tab) {
      case 0:
        return (
          <>
            <Button variant="outlined" onClick={() => handleOpen('SalaryBand')}>Add Salary Band</Button>
            <TableContainer component={Paper} sx={{ mt:1 }}>
              <Table size="small">
                <TableHead>
                  <TableRow>
                    <TableCell>Role</TableCell><TableCell>Level</TableCell><TableCell>Min</TableCell><TableCell>Mid</TableCell><TableCell>Max</TableCell><TableCell>Actions</TableCell>
                  </TableRow>
                </TableHead>
                <TableBody>
                  {salaryBands.map(item => (
                    <TableRow key={item.id}>
                      <TableCell>{item.role}</TableCell><TableCell>{item.level}</TableCell><TableCell>{item.min_value}</TableCell><TableCell>{item.mid_value}</TableCell><TableCell>{item.max_value}</TableCell>
                      <TableCell>
                        <Button size="small" onClick={() => handleOpen('SalaryBand', item)}>Edit</Button>
                        <Button size="small" color="error" onClick={() => handleDelete(item)}>Delete</Button>
                      </TableCell>
                    </TableRow>
                  ))}
                </TableBody>
              </Table>
            </TableContainer>
          </>
        );
      case 1:
        return (
          <>
            <Button variant="outlined" onClick={() => handleOpen('TeamRevenue')}>Add Team Revenue</Button>
            <TableContainer component={Paper} sx={{ mt:1 }}>
              <Table size="small">
                <TableHead>
                  <TableRow><TableCell>Team ID</TableCell><TableCell>Year</TableCell><TableCell>Revenue</TableCell><TableCell>Actions</TableCell></TableRow>
                </TableHead>
                <TableBody>
                  {teamRevenues.map(item => (
                    <TableRow key={item.id}>
                      <TableCell>{item.team}</TableCell><TableCell>{item.year}</TableCell><TableCell>{item.revenue}</TableCell>
                      <TableCell>
                        <Button size="small" onClick={() => handleOpen('TeamRevenue', item)}>Edit</Button>
                        <Button size="small" color="error" onClick={() => handleDelete(item)}>Delete</Button>
                      </TableCell>
                    </TableRow>
                  ))}
                </TableBody>
              </Table>
            </TableContainer>
          </>
        );
      case 2:
        return (
          <>
            <Button variant="outlined" onClick={() => handleOpen('MeritMatrix')}>Add Merit Matrix</Button>
            <TableContainer component={Paper} sx={{ mt:1 }}>
              <Table size="small">
                <TableHead>
                  <TableRow><TableCell>Rating</TableCell><TableCell>Range</TableCell><TableCell>Increase %</TableCell><TableCell>Actions</TableCell></TableRow>
                </TableHead>
                <TableBody>
                  {meritMatrices.map(item => (
                    <TableRow key={item.id}>
                      <TableCell>{item.performance_rating}</TableCell><TableCell>{item.compa_ratio_range}</TableCell><TableCell>{item.increase_percentage}</TableCell>
                      <TableCell>
                        <Button size="small" onClick={() => handleOpen('MeritMatrix', item)}>Edit</Button>
                        <Button size="small" color="error" onClick={() => handleDelete(item)}>Delete</Button>
                      </TableCell>
                    </TableRow>
                  ))}
                </TableBody>
              </Table>
            </TableContainer>
          </>
        );
      case 3:
        return (
          <>
            <Button variant="outlined" onClick={() => handleOpen('RevenueTrendFactor')}>Add Trend Factor</Button>
            <TableContainer component={Paper} sx={{ mt:1 }}>
              <Table size="small">
                <TableHead>
                  <TableRow><TableCell>Trend</TableCell><TableCell>Factor</TableCell><TableCell>Actions</TableCell></TableRow>
                </TableHead>
                <TableBody>
                  {revenueTrendFactors.map(item => (
                    <TableRow key={item.id}>
                      <TableCell>{item.trend_category}</TableCell><TableCell>{item.adjustment_factor}</TableCell>
                      <TableCell>
                        <Button size="small" onClick={() => handleOpen('RevenueTrendFactor', item)}>Edit</Button>
                        <Button size="small" color="error" onClick={() => handleDelete(item)}>Delete</Button>
                      </TableCell>
                    </TableRow>
                  ))}
                </TableBody>
              </Table>
            </TableContainer>
          </>
        );
      case 4:
        return (
          <>
            <Button variant="outlined" onClick={() => handleOpen('KpiAchievement')}>Add KPI Achievement</Button>
            <TableContainer component={Paper} sx={{ mt:1 }}>
              <Table size="small">
                <TableHead>
                  <TableRow><TableCell>Employee ID</TableCell><TableCell>Year</TableCell><TableCell>Inv Perf</TableCell><TableCell>Risk Mgmt</TableCell><TableCell>AUM Rev</TableCell><TableCell>Qual</TableCell><TableCell>Actions</TableCell></TableRow>
                </TableHead>
                <TableBody>
                  {kpiAchievements.map(item => (
                    <TableRow key={item.id}>
                      <TableCell>{item.employee}</TableCell><TableCell>{item.year}</TableCell><TableCell>{item.investment_performance}</TableCell><TableCell>{item.risk_management}</TableCell><TableCell>{item.aum_revenue}</TableCell><TableCell>{item.qualitative}</TableCell>
                      <TableCell>
                        <Button size="small" onClick={() => handleOpen('KpiAchievement', item)}>Edit</Button>
                        <Button size="small" color="error" onClick={() => handleDelete(item)}>Delete</Button>
                      </TableCell>
                    </TableRow>
                  ))}
                </TableBody>
              </Table>
            </TableContainer>
          </>
        );
      default:
        return null;
    }
  };

  return (
    <Box p={2} mb={4} border={1} borderColor="grey.300" borderRadius={2}>
      <Box display="flex" justifyContent="space-between" alignItems="center">
        <Typography variant="h6" gutterBottom>Configuration</Typography>
        <Box display="flex" alignItems="center">
          <input type="file" accept=".csv" onChange={e => setTeamFile(e.target.files[0])} />
          <Button size="small" variant="outlined" sx={{ ml:1 }} onClick={handleTeamUpload}>
            Upload Teams
          </Button>
          <input type="file" accept=".csv" onChange={e => { setBulkFile(e.target.files[0]); setBulkError(''); }} />
          <Button size="small" variant="contained" sx={{ ml:1 }} onClick={handleBulkUpload}>
            Bulk Upload All
          </Button>
        </Box>
      </Box>
      {bulkError && (
        <Box mt={2}>
          <Typography variant="subtitle2" color="error">Bulk Upload Error:</Typography>
          <Box component="pre" sx={{ whiteSpace: 'pre-wrap', maxHeight: 200, overflow: 'auto', fontSize: '0.75rem' }}>
            {bulkError}
          </Box>
        </Box>
      )}
      <Tabs value={tab} onChange={(e,v)=>setTab(v)}>
        <Tab label="Salary Bands" />
        <Tab label="Team Revenue" />
        <Tab label="Merit Matrix" />
        <Tab label="Trend Factors" />
        <Tab label="KPI Achievements" />
      </Tabs>
      <Box display="flex" alignItems="center" my={2}>
        <input type="file" accept=".csv" onChange={e => setUploadFile(e.target.files[0])} />
        <Button size="small" variant="contained" sx={{ ml:1 }} onClick={handleUpload}>
          Upload CSV for {['SalaryBands','TeamRevenue','MeritMatrix','TrendFactor','KPI'][tab]}
        </Button>
      </Box>
      {renderTable()}
      <Dialog open={open} onClose={handleClose} fullWidth>
        <DialogTitle>{form.id ? 'Edit' : 'Add'} {model}</DialogTitle>
        <DialogContent>{renderFields()}</DialogContent>
        <DialogActions>
          <Button onClick={handleClose}>Cancel</Button>
          <Button variant="contained" onClick={handleSave}>Save</Button>
        </DialogActions>
      </Dialog>
    </Box>
  );
}

export default ConfigPage;
