import React, { useEffect, useState } from 'react';
import {
  Box,
  Card,
  CardContent,
  LinearProgress,
  Typography,
  Alert,
  Chip,
  Stack,
  List,
  ListItem,
  ListItemIcon,
  ListItemText,
  Collapse,
  IconButton,
  Fade,
} from '@mui/material';
import {
  CheckCircle as CheckCircleIcon,
  Error as ErrorIcon,
  Info as InfoIcon,
  ExpandMore as ExpandMoreIcon,
  ExpandLess as ExpandLessIcon,
  AccessTime as TimeIcon,
  TrendingUp as TrendingUpIcon,
} from '@mui/icons-material';
import { useWebSocket } from '../hooks/useWebSocket';
import { WebSocketMessage } from '../types';

interface ProgressTrackerProps {
  analysisId: string | null;
  onComplete: (data: any) => void;
  onError: (error: string) => void;
}

interface ProgressStep {
  id: string;
  label: string;
  status: 'pending' | 'running' | 'completed' | 'error';
  message?: string;
  timestamp?: Date;
}

export const ProgressTracker: React.FC<ProgressTrackerProps> = ({
  analysisId,
  onComplete,
  onError,
}) => {
  const [progress, setProgress] = useState(0);
  const [currentMessage, setCurrentMessage] = useState('Initializing analysis...');
  const [steps, setSteps] = useState<ProgressStep[]>([
    { id: 'init', label: 'Initialize Analysis', status: 'pending' },
    { id: 'fetch', label: 'Fetch Repository Data', status: 'pending' },
    { id: 'process', label: 'Process Pull Requests', status: 'pending' },
    { id: 'calculate', label: 'Calculate Metrics', status: 'pending' },
    { id: 'complete', label: 'Analysis Complete', status: 'pending' },
  ]);
  const [isExpanded, setIsExpanded] = useState(true);
  const [startTime] = useState(new Date());
  const [elapsedTime, setElapsedTime] = useState(0);
  const [estimatedTimeRemaining, setEstimatedTimeRemaining] = useState<number | null>(null);

  const handleWebSocketMessage = (message: WebSocketMessage) => {
    console.log('Progress tracker received message:', message);

    switch (message.type) {
      case 'progress':
        if (message.progress !== undefined) {
          setProgress(message.progress);
          updateEstimatedTime(message.progress);
        }
        
        if (message.message) {
          setCurrentMessage(message.message);
          updateStepStatus(message.message);
        }
        break;

      case 'completed':
        setProgress(100);
        setCurrentMessage('Analysis completed successfully!');
        updateStepStatus('Analysis completed successfully!', 'completed');
        
        if (message.data) {
          onComplete(message.data);
        }
        break;

      case 'error':
        const errorMessage = message.error || 'Analysis failed';
        setCurrentMessage(errorMessage);
        updateStepStatus(errorMessage, 'error');
        onError(errorMessage);
        break;
    }
  };

  const updateEstimatedTime = (currentProgress: number) => {
    if (currentProgress > 0 && currentProgress < 100) {
      const elapsed = (new Date().getTime() - startTime.getTime()) / 1000;
      const rate = currentProgress / elapsed;
      const remaining = (100 - currentProgress) / rate;
      setEstimatedTimeRemaining(Math.ceil(remaining));
    } else {
      setEstimatedTimeRemaining(null);
    }
  };

  const updateStepStatus = (message: string, overrideStatus?: 'completed' | 'error') => {
    const messageLower = message.toLowerCase();
    
    setSteps(prevSteps => {
      const newSteps = [...prevSteps];
      
      // Determine which step is currently running based on message
      let activeStepId: string | null = null;
      
      if (overrideStatus === 'completed') {
        activeStepId = 'complete';
      } else if (overrideStatus === 'error') {
        // Mark current running step as error
        const runningStep = newSteps.find(step => step.status === 'running');
        if (runningStep) {
          runningStep.status = 'error';
          runningStep.message = message;
          runningStep.timestamp = new Date();
        }
        return newSteps;
      } else if (messageLower.includes('initializing') || messageLower.includes('starting')) {
        activeStepId = 'init';
      } else if (messageLower.includes('fetching') || messageLower.includes('repository')) {
        activeStepId = 'fetch';
      } else if (messageLower.includes('processing') || messageLower.includes('pull request')) {
        activeStepId = 'process';
      } else if (messageLower.includes('calculating') || messageLower.includes('metrics')) {
        activeStepId = 'calculate';
      }

      // Update step statuses
      newSteps.forEach((step, index) => {
        if (step.id === activeStepId) {
          if (overrideStatus === 'completed') {
            step.status = 'completed';
          } else {
            step.status = 'running';
          }
          step.message = message;
          step.timestamp = new Date();
          
          // Mark previous steps as completed
          for (let i = 0; i < index; i++) {
            if (newSteps[i].status === 'pending' || newSteps[i].status === 'running') {
              newSteps[i].status = 'completed';
              if (!newSteps[i].timestamp) {
                newSteps[i].timestamp = new Date();
              }
            }
          }
        }
      });

      return newSteps;
    });
  };

  const formatElapsedTime = (seconds: number): string => {
    const minutes = Math.floor(seconds / 60);
    const remainingSeconds = seconds % 60;
    
    if (minutes > 0) {
      return `${minutes}m ${remainingSeconds}s`;
    }
    return `${remainingSeconds}s`;
  };

  const getStepIcon = (status: ProgressStep['status']) => {
    switch (status) {
      case 'completed':
        return <CheckCircleIcon color="success" />;
      case 'error':
        return <ErrorIcon color="error" />;
      case 'running':
        return <TrendingUpIcon color="primary" />;
      default:
        return <TimeIcon color="disabled" />;
    }
  };

  const getStatusColor = (status: ProgressStep['status']) => {
    switch (status) {
      case 'completed':
        return 'success';
      case 'error':
        return 'error';
      case 'running':
        return 'primary';
      default:
        return 'default';
    }
  };

  const { isConnected, isConnecting, error: wsError } = useWebSocket({
    onMessage: handleWebSocketMessage,
  });

  // Connect to WebSocket when analysisId is provided
  useEffect(() => {
    if (analysisId && !isConnected && !isConnecting) {
      const ws = useWebSocket({
        onMessage: handleWebSocketMessage,
      });
      ws.connect(analysisId);
    }
  }, [analysisId, isConnected, isConnecting]);

  // Update elapsed time
  useEffect(() => {
    const interval = setInterval(() => {
      const elapsed = Math.floor((new Date().getTime() - startTime.getTime()) / 1000);
      setElapsedTime(elapsed);
    }, 1000);

    return () => clearInterval(interval);
  }, [startTime]);

  if (!analysisId) {
    return null;
  }

  return (
    <Fade in timeout={500}>
      <Card elevation={2}>
        <CardContent>
          <Box display="flex" alignItems="center" justifyContent="space-between" mb={2}>
            <Typography variant="h6" component="h3">
              Analysis Progress
            </Typography>
            <IconButton
              onClick={() => setIsExpanded(!isExpanded)}
              size="small"
            >
              {isExpanded ? <ExpandLessIcon /> : <ExpandMoreIcon />}
            </IconButton>
          </Box>

          {wsError && (
            <Alert severity="warning" sx={{ mb: 2 }}>
              WebSocket connection error: {wsError}
            </Alert>
          )}

          <Box mb={2}>
            <Box display="flex" justifyContent="space-between" alignItems="center" mb={1}>
              <Typography variant="body2" color="text.secondary">
                {currentMessage}
              </Typography>
              <Typography variant="body2" color="text.secondary">
                {progress.toFixed(0)}%
              </Typography>
            </Box>
            <LinearProgress 
              variant="determinate" 
              value={progress} 
              sx={{ height: 8, borderRadius: 4 }}
            />
          </Box>

          <Stack direction="row" spacing={1} flexWrap="wrap" mb={2}>
            <Chip
              icon={<TimeIcon />}
              label={`Elapsed: ${formatElapsedTime(elapsedTime)}`}
              size="small"
              variant="outlined"
            />
            {estimatedTimeRemaining && (
              <Chip
                icon={<TrendingUpIcon />}
                label={`Est. remaining: ${formatElapsedTime(estimatedTimeRemaining)}`}
                size="small"
                variant="outlined"
                color="primary"
              />
            )}
            <Chip
              label={isConnected ? 'Connected' : isConnecting ? 'Connecting...' : 'Disconnected'}
              size="small"
              color={isConnected ? 'success' : 'default'}
            />
          </Stack>

          <Collapse in={isExpanded}>
            <List dense>
              {steps.map((step, index) => (
                <ListItem key={step.id} disableGutters>
                  <ListItemIcon sx={{ minWidth: 36 }}>
                    {getStepIcon(step.status)}
                  </ListItemIcon>
                  <ListItemText
                    primary={
                      <Box display="flex" alignItems="center" gap={1}>
                        <Typography variant="body2">
                          {step.label}
                        </Typography>
                        <Chip
                          label={step.status}
                          size="small"
                          color={getStatusColor(step.status)}
                          sx={{ height: 20, fontSize: '0.7rem' }}
                        />
                      </Box>
                    }
                    secondary={
                      step.message && (
                        <Typography variant="caption" color="text.secondary">
                          {step.message}
                          {step.timestamp && ` • ${step.timestamp.toLocaleTimeString()}`}
                        </Typography>
                      )
                    }
                  />
                </ListItem>
              ))}
            </List>
          </Collapse>
        </CardContent>
      </Card>
    </Fade>
  );
};