import React from 'react';
import {
  Card,
  CardContent,
  Typography,
  Box,
  Grid,
} from '@mui/material';

interface MetricsChartsProps {
  data: any;
}

export const MetricsCharts: React.FC<MetricsChartsProps> = ({ data }) => {
  return (
    <Grid container spacing={2}>
      <Grid item xs={12}>
        <Card>
          <CardContent>
            <Typography variant="h6" gutterBottom>
              📊 Metrics Visualization
            </Typography>
            <Box sx={{ p: 2, textAlign: 'center' }}>
              <Typography variant="body1" color="text.secondary">
                Charts will be displayed here when data is available.
              </Typography>
              <Typography variant="body2" color="text.secondary" sx={{ mt: 1 }}>
                Data processing: {data ? 'Complete' : 'Pending'}
              </Typography>
            </Box>
          </CardContent>
        </Card>
      </Grid>
    </Grid>
  );
};