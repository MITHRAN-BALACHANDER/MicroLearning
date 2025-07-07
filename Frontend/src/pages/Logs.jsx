import React from 'react';
import { DataGrid } from '@mui/x-data-grid';
import { Box, Typography } from '@mui/material';
import Sidebar from '../components/Sidebar'
const rows = [
  { id: 1, type: 'INFO', timestamp: '2025-07-07 09:30:00', description: 'System initialized' },
  { id: 2, type: 'WARNING', timestamp: '2025-07-07 09:35:12', description: 'High memory usage' },
  { id: 3, type: 'ERROR', timestamp: '2025-07-07 09:40:23', description: 'Failed to load resource' },
  { id: 4, type: 'DEBUG', timestamp: '2025-07-07 09:42:00', description: 'Debugging enabled' },
];

const columns = [
  { field: 'id', headerName: 'S. No', width: 90 },
  { field: 'type', headerName: 'Type', width: 120 },
  { field: 'timestamp', headerName: 'Timestamp', width: 200 },
  { field: 'description', headerName: 'Description', flex: 1 },
];

const Log = () => {
  return (
   
       
    <Box
      sx={{
        height: 400,
        width: '100%',
        p: 2,
        m:6,
        fontFamily: 'Poppins, sans-serif',
      }}
    >
      <Typography variant="h6" gutterBottom sx={{ fontFamily: 'Poppins, sans-serif' }}>
        System Logs
      </Typography>
      <DataGrid
        rows={rows}
        columns={columns}
        pageSize={5}
        rowsPerPageOptions={[5]}
        disableRowSelectionOnClick
        sx={{
          fontFamily: 'Poppins, sans-serif',
          '& .MuiDataGrid-cell': {
            fontSize: '0.9rem',
          },
          '& .MuiDataGrid-columnHeaders': {
            backgroundColor: '#f3f4f6',
            fontWeight: 'bold',
          },
        }}
      />
    </Box>
  );
};

export default Log;
