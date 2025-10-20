import React from 'react';
import {
  Box,
  Card,
  CardContent,
  Typography,
  Grid,
  Chip,
  Button,
  Alert
} from '@mui/material';
import RefreshIcon from '@mui/icons-material/Refresh';

const ProfileList = ({ profiles, loading, onRefresh }) => {
  if (loading) {
    return <Alert severity="info">Loading profiles...</Alert>;
  }

  return (
    <Box>
      <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 3 }}>
        <Typography variant="h5">
          Waste Profiles ({profiles.length})
        </Typography>
        <Button 
          startIcon={<RefreshIcon />} 
          onClick={onRefresh}
          variant="outlined"
        >
          Refresh
        </Button>
      </Box>

      <Grid container spacing={3}>
        {profiles.map((profile) => (
          <Grid item xs={12} md={6} key={profile.id}>
            <Card variant="outlined">
              <CardContent>
                <Typography variant="h6" gutterBottom>
                  {profile.common_name}
                </Typography>
                
                <Typography color="textSecondary" gutterBottom>
                  {profile.generator_info.name}
                </Typography>
                
                <Typography variant="body2" gutterBottom>
                  Process: {profile.generating_process}
                </Typography>
                
                <Box sx={{ display: 'flex', gap: 1, flexWrap: 'wrap', mb: 2 }}>
                  {profile.waste_codes.map((code) => (
                    <Chip key={code} label={code} size="small" variant="outlined" />
                  ))}
                </Box>
                
                <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                  <Chip 
                    label={profile.status} 
                    color={
                      profile.status === 'approved' ? 'success' : 
                      profile.status === 'rejected' ? 'error' : 
                      'default'
                    }
                    size="small"
                  />
                  
                  {profile.ai_recommendations.length > 0 && (
                    <Chip 
                      label={`${profile.ai_recommendations.length} AI recommendations`}
                      color="primary"
                      size="small"
                    />
                  )}
                </Box>
                
                <Typography variant="caption" color="textSecondary">
                  Created: {new Date(profile.submission_date).toLocaleDateString()}
                </Typography>
              </CardContent>
            </Card>
          </Grid>
        ))}
      </Grid>

      {profiles.length === 0 && (
        <Alert severity="info">
          No profiles found. Create your first waste profile to get started.
        </Alert>
      )}
    </Box>
  );
};

export default ProfileList;