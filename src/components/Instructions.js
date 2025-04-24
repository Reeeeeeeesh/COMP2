import React from 'react';
import { Box, Typography, List, ListItem, ListItemText, Divider, Tabs, Tab } from '@mui/material';

const Instructions = () => {
  const [tabValue, setTabValue] = React.useState(0);

  const handleTabChange = (event, newValue) => {
    setTabValue(newValue);
  };

  return (
    <Box p={2} mb={4} border={1} borderColor="grey.300" borderRadius={2}>
      <Typography variant="h6" gutterBottom>How It Works</Typography>
      
      <Tabs value={tabValue} onChange={handleTabChange} aria-label="model tabs">
        <Tab label="Original Model" />
        <Tab label="Proposed Model" />
      </Tabs>
      
      <Box mt={2}>
        {tabValue === 0 ? (
          // Original Model Instructions
          <List dense>
            <ListItem>
              <ListItemText primary="1. Upload employee data via CSV." />
            </ListItem>
            <ListItem>
              <ListItemText primary="2. Adjust scenario sliders (revenue delta, adjustment factor)." />
            </ListItem>
            <ListItem>
              <ListItemText primary="3. Toggle between Pool Share or Target Bonus model." />
            </ListItem>
            <ListItem>
              <ListItemText primary="4. Click 'Run Simulation' to compute Model A & B." />
            </ListItem>
            <ListItem>
              <ListItemText primary="5. View per-employee results and aggregate summary below." />
            </ListItem>
          </List>
        ) : (
          // Proposed Model Instructions
          <List dense>
            <ListItem>
              <ListItemText 
                primary="1. Upload employee data via CSV." 
                secondary="Include role, level, team, and performance data."
              />
            </ListItem>
            <ListItem>
              <ListItemText 
                primary="2. Select performance rating and MRT status." 
                secondary="Performance rating affects merit increase via matrix."
              />
            </ListItem>
            <ListItem>
              <ListItemText 
                primary="3. Click 'Run Simulation' to compute the integrated model." 
                secondary="Combines merit increase, bonus, and regulatory requirements."
              />
            </ListItem>
            <ListItem>
              <ListItemText 
                primary="4. View detailed results with regulatory indicators." 
                secondary="Deferral applies to MRTs with bonuses over £500k."
              />
            </ListItem>
            <ListItem>
              <ListItemText 
                primary="5. Merit increase is based on performance, compa-ratio, and team revenue trend." 
                secondary="Bonus is calculated from KPI achievement or performance score."
              />
            </ListItem>
          </List>
        )}
      </Box>
    </Box>
  );
};

export default Instructions;
