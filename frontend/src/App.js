// frontend/src/App.js

import React, { useState } from 'react';
import { Container, TextField, Button, MenuItem, Typography, Box, Alert, CircularProgress, Card, CardContent, Tabs, Tab, Table, TableBody, TableCell, TableContainer, TableHead, TableRow, Paper, Fab, InputAdornment, TableSortLabel, TablePagination, IconButton, Dialog, DialogTitle, DialogContent, DialogContentText, DialogActions } from '@mui/material';
import SearchIcon from '@mui/icons-material/Search';
import AssignmentIcon from '@mui/icons-material/Assignment';
import AddCircleIcon from '@mui/icons-material/AddCircle';
import EditIcon from '@mui/icons-material/Edit';
import DeleteIcon from '@mui/icons-material/Delete';

const BACKEND_URL = 'https://solar-backend-vc9m.onrender.com';

const quoteOptions = [
  { value: '1.09', label: '1.09 kWp' },
  { value: '1.64', label: '1.64 kWp' },
  { value: '2.18', label: '2.18 kWp' },
  { value: '2.27', label: '2.27 kWp' },
  { value: '3.37', label: '3.37 kWp' },
];

const columns = [
  { id: 'name', label: 'Name' },
  { id: 'mobile', label: 'Mobile' },
  { id: 'email', label: 'Email' },
  { id: 'city', label: 'City' },
  { id: 'pincode', label: 'Pincode' },
  { id: 'quote', label: 'Quote' },
  { id: 'date', label: 'Date' },
  { id: 'ref_number', label: 'Ref Number' },
];

function descendingComparator(a, b, orderBy) {
  if (b[orderBy] < a[orderBy]) return -1;
  if (b[orderBy] > a[orderBy]) return 1;
  return 0;
}

function getComparator(order, orderBy) {
  return order === 'desc'
    ? (a, b) => descendingComparator(a, b, orderBy)
    : (a, b) => -descendingComparator(a, b, orderBy);
}

function stableSort(array, comparator) {
  const stabilized = array.map((el, idx) => [el, idx]);
  stabilized.sort((a, b) => {
    const cmp = comparator(a[0], b[0]);
    if (cmp !== 0) return cmp;
    return a[1] - b[1];
  });
  return stabilized.map(el => el[0]);
}

function App() {
  const [form, setForm] = useState({
    name: '',
    mobile: '',
    email: '',
    city: '',
    pincode: '',
    quote: '',
    date: new Date().toISOString().slice(0, 10),
  });
  const [loading, setLoading] = useState(false);
  const [alert, setAlert] = useState({ type: '', message: '' });
  const [tab, setTab] = useState(0);
  const [submissions, setSubmissions] = useState([]);
  const [fetching, setFetching] = useState(false);
  const [search, setSearch] = useState('');
  const [order, setOrder] = useState('desc');
  const [orderBy, setOrderBy] = useState('date');
  const [page, setPage] = useState(0);
  const [rowsPerPage, setRowsPerPage] = useState(5);
  const [editRef, setEditRef] = useState(null);
  const [deleteRef, setDeleteRef] = useState(null);
  const [confirmOpen, setConfirmOpen] = useState(false);

  const handleChange = (e) => {
    setForm({ ...form, [e.target.name]: e.target.value });
  };

  const handleTabChange = (event, newValue) => {
    setTab(newValue);
    if (newValue === 1) fetchSubmissions();
  };

  const handleFabClick = () => {
    setTab(0);
    setEditRef(null);
    setForm({ name: '', mobile: '', email: '', city: '', pincode: '', quote: '', date: new Date().toISOString().slice(0, 10) });
  };

  const handleEdit = (row) => {
    setForm({ ...row });
    setEditRef(row.ref_number);
    setTab(0);
  };

  const handleDelete = (ref_number) => {
    setDeleteRef(ref_number);
    setConfirmOpen(true);
  };

  const confirmDelete = async () => {
    setConfirmOpen(false);
    if (!deleteRef) return;
    try {
      await fetch(`${BACKEND_URL}/submissions/${deleteRef}`, { method: 'DELETE' });
      setSubmissions(submissions.filter(s => s.ref_number !== deleteRef));
      setAlert({ type: 'success', message: 'Submission deleted.' });
    } catch {
      setAlert({ type: 'error', message: 'Failed to delete submission.' });
    }
    setDeleteRef(null);
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    setLoading(true);
    setAlert({ type: '', message: '' });
    try {
      const url = editRef ? `${BACKEND_URL}/submissions/${editRef}` : `${BACKEND_URL}/send-quote`;
      const method = editRef ? 'PUT' : 'POST';
      const res = await fetch(url, {
        method,
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(form),
      });
      const data = await res.json();
      if (res.ok) {
        setAlert({ type: 'success', message: editRef ? 'Submission updated!' : 'Quote request sent successfully!' });
        setForm({ name: '', mobile: '', email: '', city: '', pincode: '', quote: '', date: new Date().toISOString().slice(0, 10) });
        setEditRef(null);
        if (tab === 1 || editRef) fetchSubmissions();
      } else {
        setAlert({ type: 'error', message: data.error || 'Failed to submit.' });
      }
    } catch (err) {
      setAlert({ type: 'error', message: 'Network error. Please try again.' });
    }
    setLoading(false);
  };

  const fetchSubmissions = async () => {
    setFetching(true);
    try {
      const res = await fetch(`${BACKEND_URL}/submissions`);
      const data = await res.json();
      setSubmissions(data);
    } catch (err) {
      setSubmissions([]);
    }
    setFetching(false);
  };

  const handleExportCSV = () => {
    if (!submissions.length) return;
    const header = Object.keys(submissions[0]);
    const csvRows = [header.join(',')];
    submissions.forEach(row => {
      csvRows.push(header.map(field => '"' + (row[field] || '').replace(/"/g, '""') + '"').join(','));
    });
    const csvContent = csvRows.join('\n');
    const blob = new Blob([csvContent], { type: 'text/csv' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = 'submissions.csv';
    a.click();
    URL.revokeObjectURL(url);
  };

  const handleRequestSort = (event, property) => {
    const isAsc = orderBy === property && order === 'asc';
    setOrder(isAsc ? 'desc' : 'asc');
    setOrderBy(property);
  };

  const handleChangePage = (event, newPage) => {
    setPage(newPage);
  };

  const handleChangeRowsPerPage = (event) => {
    setRowsPerPage(parseInt(event.target.value, 10));
    setPage(0);
  };

  const filteredSubmissions = submissions.filter(row =>
    Object.values(row).some(val =>
      (val || '').toString().toLowerCase().includes(search.toLowerCase())
    )
  );

  const sortedSubmissions = stableSort(filteredSubmissions, getComparator(order, orderBy));
  const paginatedSubmissions = sortedSubmissions.slice(page * rowsPerPage, page * rowsPerPage + rowsPerPage);

  return (
    // (no changes in return UI code, it's already good)
    <Container maxWidth="md" sx={{ mt: 6, position: 'relative' }}>
      {/* ... UI code remains unchanged ... */}
    </Container>
  );
}

export default App;
