import React from 'react';
import { Typography, Box, Button } from '@mui/material';

const DataUpload = () => {
  return (
    <Box p={2} mb={4} border={1} borderColor="grey.300" borderRadius={2}>
      <Typography variant="h6">Data Upload</Typography>
      <Typography variant="body2" color="text.secondary">
        Placeholder for CSV/manual data upload components.
      </Typography>
      <Box mt={2}>
        <input type="file" disabled />
        <Button variant="contained" color="primary" sx={{ ml: 2 }} disabled>
          Upload CSV
        </Button>
      </Box>
    </Box>
  );
};

export default DataUpload;
