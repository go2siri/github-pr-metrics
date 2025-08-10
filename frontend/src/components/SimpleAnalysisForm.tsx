import React, { useState } from 'react';
import {
  Card,
  CardContent,
  Typography,
  TextField,
  Button,
  Box,
  Alert,
  CircularProgress,
  Grid,
} from '@mui/material';
import { PlayArrow } from '@mui/icons-material';

interface SimpleAnalysisFormProps {
  onSubmit: (data: any) => void;
  loading?: boolean;
}

export const SimpleAnalysisForm: React.FC<SimpleAnalysisFormProps> = ({
  onSubmit,
  loading = false,
}) => {
  const [formData, setFormData] = useState({
    github_url: '',
    github_token: '',
    since: '',
    until: '',
  });
  const [error, setError] = useState<string>('');

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    setError('');

    // Basic validation
    if (!formData.github_url || !formData.github_token) {
      setError('GitHub URL and token are required');
      return;
    }

    // Validate GitHub URL
    if (!formData.github_url.includes('github.com')) {
      setError('Please enter a valid GitHub URL');
      return;
    }

    onSubmit(formData);
  };

  const handleChange = (field: string) => (e: React.ChangeEvent<HTMLInputElement>) => {
    setFormData({ ...formData, [field]: e.target.value });
  };

  return (
    <Card elevation={3}>
      <CardContent>
        <Typography variant="h5" gutterBottom align="center">
          🚀 Start Analysis
        </Typography>
        
        {error && (
          <Alert severity="error" sx={{ mb: 2 }}>
            {error}
          </Alert>
        )}

        <Box component="form" onSubmit={handleSubmit}>
          <Grid container spacing={3}>
            <Grid item xs={12}>
              <TextField
                fullWidth
                label="GitHub Repository URL"
                placeholder="https://github.com/microsoft/vscode"
                value={formData.github_url}
                onChange={handleChange('github_url')}
                required
              />
            </Grid>

            <Grid item xs={12}>
              <TextField
                fullWidth
                label="GitHub Token"
                type="password"
                placeholder="ghp_xxxxxxxxxxxxxxxxxxxx"
                value={formData.github_token}
                onChange={handleChange('github_token')}
                required
                helperText="Required for API access"
              />
            </Grid>

            <Grid item xs={6}>
              <TextField
                fullWidth
                label="Since Date (Optional)"
                type="date"
                value={formData.since}
                onChange={handleChange('since')}
                InputLabelProps={{ shrink: true }}
              />
            </Grid>

            <Grid item xs={6}>
              <TextField
                fullWidth
                label="Until Date (Optional)"
                type="date"
                value={formData.until}
                onChange={handleChange('until')}
                InputLabelProps={{ shrink: true }}
              />
            </Grid>

            <Grid item xs={12}>
              <Button
                type="submit"
                variant="contained"
                fullWidth
                size="large"
                disabled={loading}
                startIcon={loading ? <CircularProgress size={20} /> : <PlayArrow />}
              >
                {loading ? 'Analyzing...' : 'Start Analysis'}
              </Button>
            </Grid>
          </Grid>
        </Box>
      </CardContent>
    </Card>
  );
};