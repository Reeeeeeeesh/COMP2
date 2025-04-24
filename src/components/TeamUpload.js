import React, { useState } from 'react';
import { Box, Typography, Button, Alert, Paper } from '@mui/material';
import api from '../services/api';

function TeamUpload({ onUploadSuccess }) {
  const [file, setFile] = useState(null);
  const [uploading, setUploading] = useState(false);
  const [error, setError] = useState(null);
  const [success, setSuccess] = useState(false);

  const handleFileChange = (e) => {
    setFile(e.target.files[0]);
    setError(null);
    setSuccess(false);
  };

  const handleUpload = async () => {
    if (!file) {
      setError('Please select a file first');
      return;
    }

    setUploading(true);
    setError(null);
    setSuccess(false);

    const formData = new FormData();
    formData.append('file', file);

    try {
      await api.post('/teams/upload/', formData, {
        headers: {
          'Content-Type': 'multipart/form-data',
        },
      });
      setSuccess(true);
      setFile(null);
      if (onUploadSuccess) {
        onUploadSuccess();
      }
    } catch (error) {
      console.error('Error uploading teams:', error);
      setError(error.response?.data?.detail || 'Error uploading teams');
    } finally {
      setUploading(false);
    }
  };

  return (
    <Paper sx={{ p: 2, mt: 3 }}>
      <Typography variant="h6" gutterBottom>
        Team Upload
      </Typography>
      <Typography variant="body2" color="text.secondary" sx={{ mb: 2 }}>
        Upload a CSV file with team data. The file should have a "name" column for team names.
        Note: This will replace all existing teams.
      </Typography>
      
      <Box sx={{ display: 'flex', alignItems: 'center', mb: 2 }}>
        <input
          accept=".csv"
          style={{ display: 'none' }}
          id="team-upload-file"
          type="file"
          onChange={handleFileChange}
        />
        <label htmlFor="team-upload-file">
          <Button variant="outlined" component="span">
            Choose File
          </Button>
        </label>
        <Typography variant="body2" sx={{ ml: 2 }}>
          {file ? file.name : 'No file chosen'}
        </Typography>
        <Button
          variant="contained"
          onClick={handleUpload}
          disabled={!file || uploading}
          sx={{ ml: 2 }}
        >
          Upload Teams
        </Button>
      </Box>
      
      {error && <Alert severity="error" sx={{ mt: 2 }}>{error}</Alert>}
      {success && <Alert severity="success" sx={{ mt: 2 }}>Teams uploaded successfully!</Alert>}
    </Paper>
  );
}

export default TeamUpload;
