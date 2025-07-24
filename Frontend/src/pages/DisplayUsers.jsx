import React, { useState } from 'react';
import {
  Card,
  CardContent,
  Typography,
  Grid,
  TextField,
  Table,
  TableBody,
  TableCell,
  TableContainer,
  TableHead,
  TableRow,
  Paper,
  IconButton,
  Button,
  Pagination,
  Box,
} from '@mui/material';
import { Search as SearchIcon, Person as PersonIcon } from '@mui/icons-material';

const mockData = [
  { name: 'Sahana', role: 'Sales Representative', department: 'finance', empId: 1 },
  { name: 'Sahana', role: 'Marketing Head', department: 'finance', empId: 2 },
  { name: 'Sahana', role: 'HR', department: 'finance', empId: 3 },
];

const summaryCards = [
  { label: 'Total users', value: '1234', change: '+4% vs last month', color: 'green' },
  { label: 'Active users', value: '123', change: '-3% vs last month', color: 'red' },
  { label: 'New users', value: '12', change: '+6% vs last month', color: 'green' },
];

const DisplayUsers = () => {
  const [search, setSearch] = useState('');
  const [page, setPage] = useState(1);
  const rowsPerPage = 5;

  const [showForm, setShowForm] = useState(false);
  const [users, setUsers] = useState(mockData);
  const [newUser, setNewUser] = useState({
    name: '',
    role: '',
    department: '',
    empId: '',
  });

  const filteredData = users.filter((user) =>
    user.name.toLowerCase().includes(search.toLowerCase())
  );

  const paginatedData = filteredData.slice(
    (page - 1) * rowsPerPage,
    page * rowsPerPage
  );

  return (
    <Box p={3} className="ml-14">
      <Typography variant="h6" align="right" mb={2}>
        Welcome Admin
      </Typography>

      <Grid container spacing={10} mb={3}>
        {summaryCards.map((card, index) => (
          <Grid item xs={12} md={4} key={index}>
            <Card variant="outlined">
              <CardContent>
                <Typography variant="subtitle2" color="textSecondary">
                  {card.label}
                </Typography>
                <Typography variant="h5">{card.value}</Typography>
                <Typography variant="caption" color={card.color}>
                  {card.change}
                </Typography>
              </CardContent>
            </Card>
          </Grid>
        ))}
      </Grid>

      <Box display="flex" justifyContent="flex-end" mb={2}>
        <TextField
          size="small"
          variant="outlined"
          placeholder="Search"
          value={search}
          onChange={(e) => setSearch(e.target.value)}
          InputProps={{
            startAdornment: <SearchIcon color="action" sx={{ mr: 1 }} />,
          }}
        />
      </Box>

      {showForm && (
        <Box display="flex" flexDirection="column" gap={2} mb={3} p={2} border="1px solid #ccc" borderRadius={2}>
          <TextField label="Name" value={newUser.name} onChange={(e) => setNewUser({ ...newUser, name: e.target.value })} />
          <TextField label="Role" value={newUser.role} onChange={(e) => setNewUser({ ...newUser, role: e.target.value })} />
          <TextField label="Department" value={newUser.department} onChange={(e) => setNewUser({ ...newUser, department: e.target.value })} />
          <TextField label="Employee ID" type="number" value={newUser.empId} onChange={(e) => setNewUser({ ...newUser, empId: e.target.value })} />
          <Box display="flex" gap={2}>
            <Button
              variant="contained"
              color="primary"
              onClick={() => {
                setUsers([...users, { ...newUser, empId: parseInt(newUser.empId) }]);
                setNewUser({ name: '', role: '', department: '', empId: '' });
                setShowForm(false);
              }}
            >
              Save User
            </Button>
            <Button variant="outlined" color="secondary" onClick={() => setShowForm(false)}>
              Cancel
            </Button>
          </Box>
        </Box>
      )}

      <TableContainer component={Paper}>
        <Table>
          <TableHead>
            <TableRow>
              <TableCell>Employee</TableCell>
              <TableCell>Designation</TableCell>
              <TableCell>Department</TableCell>
              <TableCell>Employee ID</TableCell>
            </TableRow>
          </TableHead>
          <TableBody>
            {paginatedData.map((user, idx) => (
              <TableRow key={idx}>
                <TableCell>
                  <Box display="flex" alignItems="center" gap={1}>
                    <PersonIcon fontSize="small" color="disabled" />
                    {user.name}
                  </Box>
                </TableCell>
                <TableCell>{user.role}</TableCell>
                <TableCell>{user.department}</TableCell>
                <TableCell>{user.empId}</TableCell>
              </TableRow>
            ))}
          </TableBody>
        </Table>
      </TableContainer>

      <Box mt={3} display="flex" justifyContent="space-between" alignItems="center">
        <Pagination
          count={Math.ceil(filteredData.length / rowsPerPage)}
          page={page}
          onChange={(e, value) => setPage(value)}
          color="primary"
        />
        <Box display="flex" gap={2}>
          <Button variant="contained" color="primary" onClick={() => setShowForm(true)}>
            Add a user
          </Button>
          <Button variant="outlined" color="primary">
            Bulk upload
          </Button>
        </Box>
      </Box>
    </Box>
  );
};

export default DisplayUsers;
