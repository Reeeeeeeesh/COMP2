import React, { useState } from 'react';
import { Typography, Box, Button, CircularProgress } from '@mui/material';
import api from '../services/api';

const CsvUpload = () => {
  const [file, setFile] = useState(null);
  const [loading, setLoading] = useState(false);
  const [result, setResult] = useState(null);
  const [error, setError] = useState(null);

  const handleChange = (e) => {
    setFile(e.target.files[0]);
    setResult(null);
    setError(null);
  };

  const handleUpload = async () => {
    if (!file) return;
    setLoading(true);
    setResult(null);
    setError(null);
    const formData = new FormData();
    formData.append('file', file);
    try {
      const { data } = await api.post('/upload-data/', formData, {
        headers: { 'Content-Type': 'multipart/form-data' }
      });
      setResult(data);
    } catch (err) {
      setError(err.response?.data || err.message);
    }
    setLoading(false);
  };

  return (
    <Box>
      <Typography variant="h6">CSV Upload</Typography>
      <Box mt={1} display="flex" alignItems="center">
        <input type="file" accept=".csv" onChange={handleChange} />
        <Button
          variant="contained"
          onClick={handleUpload}
          disabled={!file || loading}
          sx={{ ml: 2 }}
        >
          {loading ? <CircularProgress size={24} /> : 'Upload CSV'}
        </Button>
      </Box>
      {result && (
        <Box mt={2}>
          <Typography>Created: {result.created.join(', ') || 'None'}</Typography>
          <Typography>Updated: {result.updated.join(', ') || 'None'}</Typography>
          {result.errors.length > 0 && (
            <Typography color="error">Errors: {JSON.stringify(result.errors)}</Typography>
          )}
        </Box>
      )}
      {error && (
        <Typography color="error">{error.error || JSON.stringify(error)}</Typography>
      )}
    </Box>
  );
};

export default CsvUpload;
