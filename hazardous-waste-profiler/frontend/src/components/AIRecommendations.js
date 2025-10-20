import React, { useState, useEffect } from 'react';
import {
  Box,
  Card,
  CardContent,
  Typography,
  Grid,
  Chip,
  Button,
  Dialog,
  DialogTitle,
  DialogContent,
  DialogActions,
  TextField,
  Alert,
  LinearProgress,
  IconButton,
  Tooltip
} from '@mui/material';
import ThumbUpIcon from '@mui/icons-material/ThumbUp';
import ThumbDownIcon from '@mui/icons-material/ThumbDown';
import RefreshIcon from '@mui/icons-material/Refresh';
import { getProfiles, submitFeedback } from '../services/api.js';

const AIRecommendations = () => {
  const [profiles, setProfiles] = useState([]);
  const [selectedProfile, setSelectedProfile] = useState(null);
  const [loading, setLoading] = useState(false);
  const [feedbackDialog, setFeedbackDialog] = useState({ open: false, recommendation: null });
  const [feedbackComment, setFeedbackComment] = useState('');

  useEffect(() => {
    loadProfiles();
  }, []);

  const loadProfiles = async () => {
    try {
      setLoading(true);
      const data = await getProfiles();
      // Filtrar perfiles que tienen recomendaciones de AI
      const profilesWithAI = data.filter(profile => 
        profile.ai_recommendations && profile.ai_recommendations.length > 0
      );
      setProfiles(profilesWithAI);
      console.log('Profiles with AI recommendations:', profilesWithAI);
    } catch (error) {
      console.error('Failed to load profiles:', error);
    } finally {
      setLoading(false);
    }
  };

  const handleFeedback = async (recommendationId, isCorrect) => {
    try {
      await submitFeedback(selectedProfile.id, recommendationId, isCorrect);
      setFeedbackDialog({ open: false, recommendation: null });
      // Reload to show updated status
      loadProfiles();
    } catch (error) {
      console.error('Failed to submit feedback:', error);
    }
  };

  const getConfidenceColor = (confidence) => {
    if (confidence >= 0.8) return 'success';
    if (confidence >= 0.6) return 'warning';
    return 'error';
  };

  return (
    <Box>
      <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 3 }}>
        <Typography variant="h5" gutterBottom>
          AI Recommendations & Validation
        </Typography>
        <Button 
          startIcon={<RefreshIcon />} 
          onClick={loadProfiles}
          variant="outlined"
          disabled={loading}
        >
          Refresh
        </Button>
      </Box>

      {loading && <LinearProgress sx={{ mb: 2 }} />}
      
      <Grid container spacing={3}>
        {profiles.map((profile) => (
          <Grid item xs={12} key={profile.id}>
            <Card 
              variant="outlined" 
              sx={{ 
                cursor: 'pointer',
                borderColor: selectedProfile?.id === profile.id ? 'primary.main' : 'divider',
                borderWidth: selectedProfile?.id === profile.id ? 2 : 1,
                '&:hover': {
                  borderColor: 'primary.main',
                  boxShadow: 1
                }
              }}
              onClick={() => setSelectedProfile(profile)}
            >
              <CardContent>
                <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start' }}>
                  <Box>
                    <Typography variant="h6">
                      {profile.common_name}
                    </Typography>
                    <Typography color="textSecondary" gutterBottom>
                      {profile.generator_info.name} • {new Date(profile.submission_date).toLocaleDateString()}
                    </Typography>
                    <Chip 
                      label={`${profile.ai_recommendations.length} AI recommendations`}
                      color="primary"
                      size="small"
                    />
                  </Box>
                  <Box sx={{ display: 'flex', flexDirection: 'column', alignItems: 'flex-end', gap: 1 }}>
                    <Chip 
                      label={profile.status}
                      color={
                        profile.status === 'approved' ? 'success' : 
                        profile.status === 'rejected' ? 'error' : 'default'
                      }
                    />
                    <Typography variant="caption" color="textSecondary">
                      Click to view details
                    </Typography>
                  </Box>
                </Box>
              </CardContent>
            </Card>
          </Grid>
        ))}
      </Grid>

      {selectedProfile && (
        <Box sx={{ mt: 4 }}>
          <Typography variant="h6" gutterBottom>
            AI Recommendations for {selectedProfile.common_name}
          </Typography>
          
          <Grid container spacing={2}>
            {selectedProfile.ai_recommendations.map((rec, index) => (
              <Grid item xs={12} key={index}>
                <Card variant="outlined" sx={{ mb: 2 }}>
                  <CardContent>
                    <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', mb: 2 }}>
                      <Typography variant="subtitle1" fontWeight="bold" sx={{ textTransform: 'capitalize' }}>
                        {rec.field_name.replace(/_/g, ' ').replace(/\./g, ' → ')}
                      </Typography>
                      <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
                        <Chip 
                          label={`${(rec.confidence * 100).toFixed(0)}% confidence`}
                          color={getConfidenceColor(rec.confidence)}
                          size="small"
                        />
                        {rec.is_correct !== null && (
                          <Chip 
                            label={rec.is_correct ? 'Confirmed' : 'Rejected'}
                            color={rec.is_correct ? 'success' : 'error'}
                            size="small"
                          />
                        )}
                      </Box>
                    </Box>

                    <Grid container spacing={2}>
                      <Grid item xs={12} sm={6}>
                        <Typography variant="body2" color="textSecondary">
                          Current Value:
                        </Typography>
                        <Typography variant="body1" sx={{ fontFamily: 'monospace', backgroundColor: '#f5f5f5', p: 1, borderRadius: 1 }}>
                          {String(rec.current_value) || 'Empty'}
                        </Typography>
                      </Grid>
                      <Grid item xs={12} sm={6}>
                        <Typography variant="body2" color="textSecondary">
                          Recommended Value:
                        </Typography>
                        <Typography variant="body1" color="primary.main" sx={{ fontFamily: 'monospace', backgroundColor: '#e3f2fd', p: 1, borderRadius: 1 }}>
                          {rec.recommended_value}
                        </Typography>
                      </Grid>
                    </Grid>

                    <Box sx={{ mt: 2 }}>
                      <Typography variant="body2" color="textSecondary" gutterBottom>
                        Reasoning:
                      </Typography>
                      <Typography variant="body1" sx={{ fontStyle: 'italic' }}>
                        {rec.reasoning}
                      </Typography>
                    </Box>

                    {rec.is_correct === null && (
                      <Box sx={{ mt: 2, display: 'flex', gap: 1, alignItems: 'center' }}>
                        <Typography variant="body2" color="textSecondary">
                          Is this recommendation helpful?
                        </Typography>
                        <Tooltip title="Mark as correct">
                          <IconButton 
                            color="success" 
                            onClick={() => handleFeedback(index, true)}
                            size="small"
                          >
                            <ThumbUpIcon />
                          </IconButton>
                        </Tooltip>
                        <Tooltip title="Mark as incorrect">
                          <IconButton 
                            color="error"
                            onClick={() => handleFeedback(index, false)}
                            size="small"
                          >
                            <ThumbDownIcon />
                          </IconButton>
                        </Tooltip>
                      </Box>
                    )}
                  </CardContent>
                </Card>
              </Grid>
            ))}
          </Grid>
        </Box>
      )}

      {!loading && profiles.length === 0 && (
        <Alert severity="info" sx={{ mt: 2 }}>
          <Typography variant="body1" gutterBottom>
            No AI recommendations available yet.
          </Typography>
          <Typography variant="body2">
            Create a new waste profile to see AI-powered validation suggestions. The AI will analyze your profile and provide recommendations for improvements.
          </Typography>
        </Alert>
      )}
    </Box>
  );
};

export default AIRecommendations;