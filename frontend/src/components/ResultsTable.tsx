import React, { useState, useMemo } from 'react';
import {
  Box,
  Card,
  CardContent,
  Typography,
  TextField,
  Button,
  MenuItem,
  Stack,
  Chip,
  IconButton,
  Tooltip,
  Alert,
} from '@mui/material';
import {
  DataGrid,
  GridColDef,
  GridToolbarContainer,
  GridToolbarExport,
  GridToolbarFilterButton,
  GridToolbarColumnsButton,
  GridToolbarDensitySelector,
  GridValueGetterParams,
} from '@mui/x-data-grid';
import {
  Download as DownloadIcon,
  OpenInNew as OpenInNewIcon,
  FilterList as FilterIcon,
} from '@mui/icons-material';
import { format, parseISO, differenceInHours } from 'date-fns';
import { PRMetric, FilterOptions, SortOption } from '../types';
import { apiService } from '../services/api';

interface ResultsTableProps {
  data: PRMetric[];
  analysisId: string;
  isLoading?: boolean;
}

interface CustomToolbarProps {
  onExportCSV: () => void;
  isExporting: boolean;
}

const CustomToolbar: React.FC<CustomToolbarProps> = ({ onExportCSV, isExporting }) => {
  return (
    <GridToolbarContainer>
      <GridToolbarColumnsButton />
      <GridToolbarFilterButton />
      <GridToolbarDensitySelector />
      <GridToolbarExport />
      <Button
        startIcon={<DownloadIcon />}
        onClick={onExportCSV}
        disabled={isExporting}
        sx={{ ml: 1 }}
      >
        {isExporting ? 'Exporting...' : 'Export CSV'}
      </Button>
    </GridToolbarContainer>
  );
};

export const ResultsTable: React.FC<ResultsTableProps> = ({
  data,
  analysisId,
  isLoading = false,
}) => {
  const [filters, setFilters] = useState<FilterOptions>({});
  const [isExporting, setIsExporting] = useState(false);
  const [exportError, setExportError] = useState<string | null>(null);

  const formatDate = (dateString: string | null): string => {
    if (!dateString) return 'N/A';
    try {
      return format(parseISO(dateString), 'MMM dd, yyyy HH:mm');
    } catch {
      return 'Invalid Date';
    }
  };

  const formatHours = (hours: number | null): string => {
    if (hours === null || hours === undefined) return 'N/A';
    
    if (hours < 1) {
      return `${Math.round(hours * 60)}m`;
    } else if (hours < 24) {
      return `${hours.toFixed(1)}h`;
    } else {
      const days = Math.floor(hours / 24);
      const remainingHours = Math.round(hours % 24);
      return `${days}d ${remainingHours}h`;
    }
  };

  const getStateChip = (state: string) => {
    const color = state === 'merged' ? 'success' : state === 'closed' ? 'error' : 'default';
    return <Chip label={state} size="small" color={color} />;
  };

  const columns: GridColDef[] = [
    {
      field: 'pr_number',
      headerName: 'PR #',
      width: 80,
      renderCell: (params) => (
        <Tooltip title="Open PR in GitHub">
          <IconButton
            size="small"
            onClick={() => {
              // Extract repo URL from the data or context
              // This would need to be passed as a prop or stored in context
              const repoUrl = 'https://github.com/owner/repo'; // This should be dynamic
              window.open(`${repoUrl}/pull/${params.value}`, '_blank');
            }}
          >
            #{params.value}
            <OpenInNewIcon fontSize="small" sx={{ ml: 0.5 }} />
          </IconButton>
        </Tooltip>
      ),
    },
    {
      field: 'title',
      headerName: 'Title',
      width: 300,
      renderCell: (params) => (
        <Tooltip title={params.value}>
          <Typography variant="body2" noWrap>
            {params.value}
          </Typography>
        </Tooltip>
      ),
    },
    {
      field: 'author',
      headerName: 'Author',
      width: 120,
    },
    {
      field: 'state',
      headerName: 'State',
      width: 100,
      renderCell: (params) => getStateChip(params.value),
    },
    {
      field: 'created_at',
      headerName: 'Created',
      width: 140,
      valueFormatter: (params) => formatDate(params.value),
    },
    {
      field: 'merged_at',
      headerName: 'Merged',
      width: 140,
      valueFormatter: (params) => formatDate(params.value),
    },
    {
      field: 'review_time_hours',
      headerName: 'Review Time',
      width: 120,
      valueFormatter: (params) => formatHours(params.value),
      type: 'number',
    },
    {
      field: 'time_to_merge_hours',
      headerName: 'Merge Time',
      width: 120,
      valueFormatter: (params) => formatHours(params.value),
      type: 'number',
    },
    {
      field: 'lines_added',
      headerName: 'Lines +',
      width: 100,
      type: 'number',
      renderCell: (params) => (
        <Typography color="success.main" variant="body2">
          +{params.value}
        </Typography>
      ),
    },
    {
      field: 'lines_deleted',
      headerName: 'Lines -',
      width: 100,
      type: 'number',
      renderCell: (params) => (
        <Typography color="error.main" variant="body2">
          -{params.value}
        </Typography>
      ),
    },
    {
      field: 'files_changed',
      headerName: 'Files',
      width: 80,
      type: 'number',
    },
    {
      field: 'commits',
      headerName: 'Commits',
      width: 90,
      type: 'number',
    },
    {
      field: 'reviews_count',
      headerName: 'Reviews',
      width: 90,
      type: 'number',
    },
    {
      field: 'review_comments',
      headerName: 'Comments',
      width: 100,
      type: 'number',
    },
  ];

  const handleExportCSV = async () => {
    setIsExporting(true);
    setExportError(null);

    try {
      const blob = await apiService.exportCSV(analysisId);
      
      // Create download link
      const url = window.URL.createObjectURL(blob);
      const link = document.createElement('a');
      link.href = url;
      link.download = `pr-metrics-${analysisId}-${format(new Date(), 'yyyy-MM-dd')}.csv`;
      document.body.appendChild(link);
      link.click();
      document.body.removeChild(link);
      window.URL.revokeObjectURL(url);

    } catch (error) {
      console.error('Export error:', error);
      setExportError(
        error instanceof Error
          ? error.message
          : 'Failed to export CSV. Please try again.'
      );
    } finally {
      setIsExporting(false);
    }
  };

  const filteredData = useMemo(() => {
    if (!filters || Object.keys(filters).length === 0) {
      return data;
    }

    return data.filter((row) => {
      if (filters.author && !row.author.toLowerCase().includes(filters.author.toLowerCase())) {
        return false;
      }

      if (filters.state && row.state !== filters.state) {
        return false;
      }

      if (filters.dateRange) {
        const createdDate = parseISO(row.created_at);
        if (createdDate < filters.dateRange.start || createdDate > filters.dateRange.end) {
          return false;
        }
      }

      if (filters.minReviewTime && (row.review_time_hours ?? 0) < filters.minReviewTime) {
        return false;
      }

      if (filters.maxReviewTime && (row.review_time_hours ?? Infinity) > filters.maxReviewTime) {
        return false;
      }

      return true;
    });
  }, [data, filters]);

  const uniqueAuthors = useMemo(() => {
    return Array.from(new Set(data.map(row => row.author))).sort();
  }, [data]);

  const uniqueStates = useMemo(() => {
    return Array.from(new Set(data.map(row => row.state))).sort();
  }, [data]);

  if (!data || data.length === 0) {
    return (
      <Card>
        <CardContent>
          <Typography variant="h6" gutterBottom>
            Pull Request Data
          </Typography>
          <Alert severity="info">
            No pull request data available. Start an analysis to see results here.
          </Alert>
        </CardContent>
      </Card>
    );
  }

  return (
    <Card>
      <CardContent>
        <Typography variant="h6" gutterBottom display="flex" alignItems="center" gap={1}>
          <FilterIcon />
          Pull Request Data ({filteredData.length} of {data.length} PRs)
        </Typography>

        {exportError && (
          <Alert severity="error" sx={{ mb: 2 }}>
            {exportError}
          </Alert>
        )}

        {/* Filters */}
        <Stack direction="row" spacing={2} mb={3} flexWrap="wrap">
          <TextField
            label="Filter by Author"
            select
            value={filters.author || ''}
            onChange={(e) => setFilters(prev => ({ ...prev, author: e.target.value || undefined }))}
            size="small"
            sx={{ minWidth: 150 }}
          >
            <MenuItem value="">All Authors</MenuItem>
            {uniqueAuthors.map(author => (
              <MenuItem key={author} value={author}>
                {author}
              </MenuItem>
            ))}
          </TextField>

          <TextField
            label="Filter by State"
            select
            value={filters.state || ''}
            onChange={(e) => setFilters(prev => ({ ...prev, state: e.target.value || undefined }))}
            size="small"
            sx={{ minWidth: 120 }}
          >
            <MenuItem value="">All States</MenuItem>
            {uniqueStates.map(state => (
              <MenuItem key={state} value={state}>
                <Chip label={state} size="small" color={state === 'merged' ? 'success' : state === 'closed' ? 'error' : 'default'} />
              </MenuItem>
            ))}
          </TextField>

          <TextField
            label="Min Review Time (hours)"
            type="number"
            value={filters.minReviewTime || ''}
            onChange={(e) => setFilters(prev => ({ ...prev, minReviewTime: e.target.value ? Number(e.target.value) : undefined }))}
            size="small"
            sx={{ minWidth: 140 }}
          />

          <TextField
            label="Max Review Time (hours)"
            type="number"
            value={filters.maxReviewTime || ''}
            onChange={(e) => setFilters(prev => ({ ...prev, maxReviewTime: e.target.value ? Number(e.target.value) : undefined }))}
            size="small"
            sx={{ minWidth: 140 }}
          />
        </Stack>

        {/* Data Grid */}
        <Box sx={{ height: 600, width: '100%' }}>
          <DataGrid
            rows={filteredData}
            columns={columns}
            loading={isLoading}
            pageSizeOptions={[10, 25, 50, 100]}
            initialState={{
              pagination: { paginationModel: { pageSize: 25 } },
            }}
            disableRowSelectionOnClick
            slots={{
              toolbar: CustomToolbar,
            }}
            slotProps={{
              toolbar: {
                onExportCSV: handleExportCSV,
                isExporting,
              },
            }}
            sx={{
              '& .MuiDataGrid-cell': {
                borderRight: 1,
                borderColor: 'divider',
              },
              '& .MuiDataGrid-columnHeaders': {
                backgroundColor: 'background.paper',
                borderBottom: 2,
                borderColor: 'primary.main',
              },
            }}
          />
        </Box>
      </CardContent>
    </Card>
  );
};