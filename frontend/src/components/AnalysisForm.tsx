import React, { useState } from 'react';
import {
  Box,
  Card,
  CardContent,
  TextField,
  Button,
  Typography,
  Alert,
  CircularProgress,
  InputAdornment,
  IconButton,
  Divider,
  Chip,
  Stack,
} from '@mui/material';
import {
  GitHub as GitHubIcon,
  Visibility,
  VisibilityOff,
  Analytics as AnalyticsIcon,
  DateRange as DateRangeIcon,
} from '@mui/icons-material';
import { DatePicker } from '@mui/x-date-pickers/DatePicker';
import { LocalizationProvider } from '@mui/x-date-pickers/LocalizationProvider';
import { AdapterDateFns } from '@mui/x-date-pickers/AdapterDateFns';
import { format } from 'date-fns';
import { AnalysisRequest } from '../types';
import { apiService } from '../services/api';

interface AnalysisFormProps {
  onAnalysisStart: (analysisId: string, request: AnalysisRequest) => void;
  isLoading?: boolean;
}

interface FormData {
  githubUrl: string;
  githubToken: string;
  startDate: Date | null;
  endDate: Date | null;
}

interface FormErrors {
  githubUrl?: string;
  githubToken?: string;
  startDate?: string;
  endDate?: string;
  dateRange?: string;
}

export const AnalysisForm: React.FC<AnalysisFormProps> = ({
  onAnalysisStart,
  isLoading = false,
}) => {
  const [formData, setFormData] = useState<FormData>({
    githubUrl: '',
    githubToken: '',
    startDate: null,
    endDate: null,
  });

  const [errors, setErrors] = useState<FormErrors>({});
  const [showToken, setShowToken] = useState(false);
  const [isValidating, setIsValidating] = useState(false);
  const [submitError, setSubmitError] = useState<string | null>(null);

  const validateForm = (): boolean => {
    const newErrors: FormErrors = {};

    // Validate GitHub URL
    const urlValidation = apiService.validateGitHubUrl(formData.githubUrl);
    if (!urlValidation.valid) {
      newErrors.githubUrl = urlValidation.message;
    }

    // Validate GitHub Token
    if (!formData.githubToken.trim()) {
      newErrors.githubToken = 'GitHub token is required';
    } else if (formData.githubToken.length < 10) {
      newErrors.githubToken = 'GitHub token appears to be too short';
    }

    // Validate date range
    const dateValidation = apiService.validateDateRange(
      formData.startDate ? format(formData.startDate, 'yyyy-MM-dd') : undefined,
      formData.endDate ? format(formData.endDate, 'yyyy-MM-dd') : undefined
    );
    
    if (!dateValidation.valid) {
      newErrors.dateRange = dateValidation.message;
    }

    setErrors(newErrors);
    return Object.keys(newErrors).length === 0;
  };

  const handleInputChange = (field: keyof FormData) => (
    event: React.ChangeEvent<HTMLInputElement>
  ) => {
    setFormData(prev => ({
      ...prev,
      [field]: event.target.value,
    }));

    // Clear specific field error when user starts typing
    if (errors[field]) {
      setErrors(prev => ({
        ...prev,
        [field]: undefined,
      }));
    }
  };

  const handleDateChange = (field: 'startDate' | 'endDate') => (date: Date | null) => {
    setFormData(prev => ({
      ...prev,
      [field]: date,
    }));

    // Clear date-related errors
    setErrors(prev => ({
      ...prev,
      [field]: undefined,
      dateRange: undefined,
    }));
  };

  const handleSubmit = async (event: React.FormEvent) => {
    event.preventDefault();
    setSubmitError(null);

    if (!validateForm()) {
      return;
    }

    setIsValidating(true);

    try {
      // Test GitHub token before starting analysis
      const tokenTest = await apiService.testGitHubToken(
        formData.githubToken,
        formData.githubUrl
      );

      if (!tokenTest.valid) {
        setErrors({ githubToken: tokenTest.message });
        return;
      }

      // Prepare analysis request
      const request: AnalysisRequest = {
        github_url: formData.githubUrl.trim(),
        github_token: formData.githubToken.trim(),
      };

      if (formData.startDate) {
        request.start_date = format(formData.startDate, 'yyyy-MM-dd');
      }

      if (formData.endDate) {
        request.end_date = format(formData.endDate, 'yyyy-MM-dd');
      }

      // Start analysis
      const response = await apiService.startAnalysis(request);
      onAnalysisStart(response.task_id, request);

    } catch (error) {
      console.error('Analysis start error:', error);
      setSubmitError(
        error instanceof Error 
          ? error.message 
          : 'Failed to start analysis. Please try again.'
      );
    } finally {
      setIsValidating(false);
    }
  };

  const isFormDisabled = isLoading || isValidating;

  return (
    <LocalizationProvider dateAdapter={AdapterDateFns}>
      <Card elevation={2}>
        <CardContent>
          <Box display="flex" alignItems="center" gap={2} mb={3}>
            <AnalyticsIcon color="primary" fontSize="large" />
            <Typography variant="h5" component="h2">
              GitHub PR Analysis
            </Typography>
          </Box>

          <Typography variant="body2" color="text.secondary" mb={3}>
            Analyze pull request metrics for any GitHub repository. Get insights on review times,
            merge patterns, and team productivity.
          </Typography>

          {submitError && (
            <Alert severity="error" sx={{ mb: 3 }}>
              {submitError}
            </Alert>
          )}

          <form onSubmit={handleSubmit}>
            <Stack spacing={3}>
              {/* GitHub URL */}
              <TextField
                fullWidth
                label="GitHub Repository URL"
                placeholder="https://github.com/owner/repository"
                value={formData.githubUrl}
                onChange={handleInputChange('githubUrl')}
                error={!!errors.githubUrl}
                helperText={errors.githubUrl || 'Enter the GitHub repository URL to analyze'}
                disabled={isFormDisabled}
                InputProps={{
                  startAdornment: (
                    <InputAdornment position="start">
                      <GitHubIcon color="action" />
                    </InputAdornment>
                  ),
                }}
              />

              {/* GitHub Token */}
              <TextField
                fullWidth
                type={showToken ? 'text' : 'password'}
                label="GitHub Personal Access Token"
                placeholder="ghp_xxxxxxxxxxxxxxxxxxxx"
                value={formData.githubToken}
                onChange={handleInputChange('githubToken')}
                error={!!errors.githubToken}
                helperText={
                  errors.githubToken || 
                  'Required for accessing GitHub API. Create one at github.com/settings/tokens'
                }
                disabled={isFormDisabled}
                InputProps={{
                  endAdornment: (
                    <InputAdornment position="end">
                      <IconButton
                        onClick={() => setShowToken(!showToken)}
                        edge="end"
                        disabled={isFormDisabled}
                      >
                        {showToken ? <VisibilityOff /> : <Visibility />}
                      </IconButton>
                    </InputAdornment>
                  ),
                }}
              />

              <Divider>
                <Chip 
                  icon={<DateRangeIcon />} 
                  label="Date Range (Optional)" 
                  variant="outlined" 
                  size="small" 
                />
              </Divider>

              {/* Date Range */}
              <Box display="flex" gap={2} flexWrap="wrap">
                <DatePicker
                  label="Start Date"
                  value={formData.startDate}
                  onChange={handleDateChange('startDate')}
                  disabled={isFormDisabled}
                  slotProps={{
                    textField: {
                      fullWidth: true,
                      error: !!errors.startDate,
                      helperText: errors.startDate,
                    },
                  }}
                />
                
                <DatePicker
                  label="End Date"
                  value={formData.endDate}
                  onChange={handleDateChange('endDate')}
                  disabled={isFormDisabled}
                  slotProps={{
                    textField: {
                      fullWidth: true,
                      error: !!errors.endDate,
                      helperText: errors.endDate,
                    },
                  }}
                />
              </Box>

              {errors.dateRange && (
                <Alert severity="error">
                  {errors.dateRange}
                </Alert>
              )}

              {/* Submit Button */}
              <Box display="flex" justifyContent="center" mt={2}>
                <Button
                  type="submit"
                  variant="contained"
                  size="large"
                  disabled={isFormDisabled}
                  startIcon={
                    isValidating ? (
                      <CircularProgress size={20} />
                    ) : (
                      <AnalyticsIcon />
                    )
                  }
                  sx={{ minWidth: 200, py: 1.5 }}
                >
                  {isValidating ? 'Validating...' : isLoading ? 'Analyzing...' : 'Start Analysis'}
                </Button>
              </Box>
            </Stack>
          </form>
        </CardContent>
      </Card>
    </LocalizationProvider>
  );
};