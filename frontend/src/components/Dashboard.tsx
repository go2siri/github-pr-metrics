import React, { useState } from 'react';
import {
  Container,
  Typography,
  Box,
  Alert,
  Card,
  CardContent,
  Grid,
  LinearProgress,
  Button,
  Table,
  TableBody,
  TableCell,
  TableContainer,
  TableHead,
  TableRow,
  Paper,
} from '@mui/material';
import { PlayArrow, Download } from '@mui/icons-material';
import { SimpleAnalysisForm } from './SimpleAnalysisForm';
import { apiService } from '../services/api';

export const Dashboard: React.FC = () => {
  const [loading, setLoading] = useState(false);
  const [progress, setProgress] = useState(0);
  const [results, setResults] = useState<any>(null);
  const [error, setError] = useState<string>('');
  const [currentTaskId, setCurrentTaskId] = useState<string>('');

  const handleAnalysis = async (formData: any) => {
    try {
      setLoading(true);
      setError('');
      setProgress(0);
      setResults(null);

      // Start analysis
      const response = await apiService.startAnalysis(formData);
      setCurrentTaskId(response.task_id);
      
      // Connect to WebSocket for progress updates
      connectToWebSocket(response.task_id);
      
      // Poll for results
      pollForResults(response.task_id);
      
    } catch (err: any) {
      setError(err.message || 'Analysis failed');
      setLoading(false);
    }
  };

  const connectToWebSocket = (taskId: string) => {
    const ws = new WebSocket(`ws://localhost:8000/ws/${taskId}`);
    
    ws.onmessage = (event) => {
      const data = JSON.parse(event.data);
      
      if (data.type === 'progress') {
        setProgress(data.data.progress);
      } else if (data.type === 'completed') {
        setResults(data.data);
        setLoading(false);
        ws.close();
      } else if (data.type === 'error') {
        setError(data.data.error);
        setLoading(false);
        ws.close();
      }
    };
    
    ws.onerror = () => {
      console.log('WebSocket error, falling back to polling');
    };
  };

  const pollForResults = async (taskId: string) => {
    const maxAttempts = 60; // 5 minutes
    let attempts = 0;
    
    const poll = async () => {
      try {
        const result = await apiService.getAnalysisStatus(taskId);
        
        if (result.status === 'completed') {
          setResults(result);
          setLoading(false);
          return;
        }
        
        if (result.status === 'failed') {
          setError(result.error || 'Analysis failed');
          setLoading(false);
          return;
        }
        
        // Continue polling
        attempts++;
        if (attempts < maxAttempts) {
          setTimeout(poll, 3000);
        } else {
          setError('Analysis timeout');
          setLoading(false);
        }
      } catch (err: any) {
        setError(err.message);
        setLoading(false);
      }
    };
    
    setTimeout(poll, 2000);
  };

  const handleExport = async () => {
    if (!currentTaskId) return;
    
    try {
      await apiService.exportCSV(currentTaskId);
      // File should download automatically
    } catch (err: any) {
      setError(err.message || 'Export failed');
    }
  };

  const handleNewAnalysis = () => {
    setResults(null);
    setError('');
    setProgress(0);
    setLoading(false);
    setCurrentTaskId('');
  };

  return (
    <Container maxWidth="lg">
      <Box sx={{ py: 4 }}>
        <Typography variant="h3" component="h1" gutterBottom align="center">
          📊 GitHub PR Metrics Analyzer
        </Typography>
        <Typography variant="h6" color="text.secondary" align="center" sx={{ mb: 4 }}>
          Analyze Pull Request metrics with real-time insights
        </Typography>

        {error && (
          <Alert severity="error" sx={{ mb: 3 }} onClose={() => setError('')}>
            {error}
          </Alert>
        )}

        {!loading && !results && (
          <Box sx={{ maxWidth: 800, mx: 'auto' }}>
            <SimpleAnalysisForm onSubmit={handleAnalysis} loading={loading} />
          </Box>
        )}

        {loading && (
          <Card sx={{ maxWidth: 800, mx: 'auto', mb: 3 }}>
            <CardContent>
              <Typography variant="h6" gutterBottom>
                🔄 Analysis in Progress
              </Typography>
              <LinearProgress variant="determinate" value={progress} sx={{ mb: 2 }} />
              <Typography variant="body2" color="text.secondary">
                Progress: {progress}%
              </Typography>
            </CardContent>
          </Card>
        )}

        {results && (
          <Box sx={{ mt: 4 }}>
            <Card sx={{ mb: 3 }}>
              <CardContent>
                <Box display="flex" justifyContent="space-between" alignItems="center" mb={2}>
                  <Typography variant="h5" color="success.main">
                    ✅ Analysis Complete!
                  </Typography>
                  <Box>
                    <Button
                      variant="outlined"
                      onClick={handleExport}
                      startIcon={<Download />}
                      sx={{ mr: 2 }}
                    >
                      Export CSV
                    </Button>
                    <Button
                      variant="contained"
                      onClick={handleNewAnalysis}
                      startIcon={<PlayArrow />}
                    >
                      New Analysis
                    </Button>
                  </Box>
                </Box>

                {/* Summary Cards */}
                <Grid container spacing={2} sx={{ mb: 3 }}>
                  <Grid item xs={12} sm={3}>
                    <Card sx={{ bgcolor: 'primary.light', color: 'primary.contrastText' }}>
                      <CardContent sx={{ textAlign: 'center' }}>
                        <Typography variant="h4">{results.analysis_metadata?.total_prs_processed || 0}</Typography>
                        <Typography variant="body2">Total PRs</Typography>
                      </CardContent>
                    </Card>
                  </Grid>
                  <Grid item xs={12} sm={3}>
                    <Card sx={{ bgcolor: 'success.light', color: 'success.contrastText' }}>
                      <CardContent sx={{ textAlign: 'center' }}>
                        <Typography variant="h4">{results.analysis_metadata?.total_repositories || 0}</Typography>
                        <Typography variant="body2">Repositories</Typography>
                      </CardContent>
                    </Card>
                  </Grid>
                  <Grid item xs={12} sm={3}>
                    <Card sx={{ bgcolor: 'info.light', color: 'info.contrastText' }}>
                      <CardContent sx={{ textAlign: 'center' }}>
                        <Typography variant="h4">{results.analysis_metadata?.total_developers || 0}</Typography>
                        <Typography variant="body2">Developers</Typography>
                      </CardContent>
                    </Card>
                  </Grid>
                  <Grid item xs={12} sm={3}>
                    <Card sx={{ bgcolor: 'warning.light', color: 'warning.contrastText' }}>
                      <CardContent sx={{ textAlign: 'center' }}>
                        <Typography variant="h4">
                          {results.analysis_metadata?.analysis_duration 
                            ? `${(results.analysis_metadata.analysis_duration * 1000).toFixed(0)}ms` 
                            : 'N/A'
                          }
                        </Typography>
                        <Typography variant="body2">Analysis Time</Typography>
                      </CardContent>
                    </Card>
                  </Grid>
                </Grid>

                {/* Data Table */}
                <Typography variant="h6" gutterBottom>
                  📋 Developer Details
                </Typography>
                <TableContainer component={Paper}>
                  <Table>
                    <TableHead>
                      <TableRow>
                        <TableCell><strong>Developer</strong></TableCell>
                        <TableCell align="right"><strong>Total PRs</strong></TableCell>
                        <TableCell align="right"><strong>Open</strong></TableCell>
                        <TableCell align="right"><strong>Merged</strong></TableCell>
                        <TableCell align="right"><strong>Closed</strong></TableCell>
                        <TableCell align="right"><strong>Merge Rate</strong></TableCell>
                      </TableRow>
                    </TableHead>
                    <TableBody>
                      {results.repository_metrics?.[0]?.developers && Object.entries(results.repository_metrics[0].developers).slice(0, 10).map(([devName, devData]: [string, any]) => (
                        <TableRow key={devName}>
                          <TableCell component="th" scope="row">
                            {devName}
                          </TableCell>
                          <TableCell align="right">{devData.basic_metrics?.total || 0}</TableCell>
                          <TableCell align="right">{devData.basic_metrics?.open || 0}</TableCell>
                          <TableCell align="right">{devData.basic_metrics?.merged || 0}</TableCell>
                          <TableCell align="right">{devData.basic_metrics?.closed || 0}</TableCell>
                          <TableCell align="right">
                            {devData.productivity_metrics?.merge_rate_percent?.toFixed(1) || '0.0'}%
                          </TableCell>
                        </TableRow>
                      ))}
                    </TableBody>
                  </Table>
                </TableContainer>
              </CardContent>
            </Card>
          </Box>
        )}
      </Box>
    </Container>
  );
};