import React, { useState, useEffect } from 'react';
import { ThemeProvider, createTheme } from '@mui/material/styles';
import { CssBaseline, Container, Box, AppBar, Toolbar, Typography, IconButton } from '@mui/material';
import { Brightness4, Brightness7, GitHub } from '@mui/icons-material';
import { Dashboard } from './components/Dashboard';

function App() {
  const [darkMode, setDarkMode] = useState(false);

  const theme = createTheme({
    palette: {
      mode: darkMode ? 'dark' : 'light',
      primary: {
        main: '#1976d2',
      },
      secondary: {
        main: '#dc004e',
      },
    },
  });

  const toggleDarkMode = () => {
    setDarkMode(!darkMode);
  };

  return (
    <ThemeProvider theme={theme}>
      <CssBaseline />
      <Box sx={{ flexGrow: 1 }}>
        <AppBar position="static" elevation={2}>
          <Toolbar>
            <GitHub sx={{ mr: 2 }} />
            <Typography variant="h6" component="div" sx={{ flexGrow: 1 }}>
              GitHub PR Metrics Analyzer
            </Typography>
            <IconButton color="inherit" onClick={toggleDarkMode}>
              {darkMode ? <Brightness7 /> : <Brightness4 />}
            </IconButton>
          </Toolbar>
        </AppBar>
        
        <Container maxWidth="lg" sx={{ py: 4 }}>
          <Dashboard />
        </Container>
      </Box>
    </ThemeProvider>
  );
}

export default App;