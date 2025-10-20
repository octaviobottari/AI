// frontend/src/App.js
import React, { useState, useEffect } from 'react';
import { 
  Container, 
  Typography, 
  AppBar, 
  Toolbar, 
  Paper, 
  Grid,
  Card,
  CardContent,
  Alert,
  CircularProgress,
  Box,
  Tabs,
  Tab
} from '@mui/material';
import { ThemeProvider, createTheme } from '@mui/material/styles';
import ProfileForm from './components/ProfileForm.js';
import ProfileList from './components/ProfileList.js';
import AIRecommendations from './components/AIRecommendations.js';
import { getProfiles, createProfile, validateProfile } from './services/api.js';

const theme = createTheme({
  palette: {
    primary: {
      main: '#2E7D32', // Republic Services green
    },
    secondary: {
      main: '#FF6F00',
    },
  },
});

function TabPanel({ children, value, index, ...other }) {
  return (
    <div role="tabpanel" hidden={value !== index} {...other}>
      {value === index && <Box sx={{ p: 3 }}>{children}</Box>}
    </div>
  );
}

function App() {
  const [tabValue, setTabValue] = useState(0);
  const [profiles, setProfiles] = useState([]);
  const [loading, setLoading] = useState(false);
  const [message, setMessage] = useState({ type: '', text: '' });

  useEffect(() => {
    loadProfiles();
  }, []);

  const loadProfiles = async () => {
    try {
      setLoading(true);
      const data = await getProfiles();
      setProfiles(data);
    } catch (error) {
      showMessage('error', 'Failed to load profiles');
    } finally {
      setLoading(false);
    }
  };

  const handleProfileSubmit = async (profileData) => {
    try {
      setLoading(true);
      const newProfile = await createProfile(profileData);
      setProfiles(prev => [newProfile, ...prev]);
      showMessage('success', 'Profile created successfully! AI validation in progress...');
      setTabValue(1); // Switch to profiles tab
    } catch (error) {
      showMessage('error', 'Failed to create profile');
    } finally {
      setLoading(false);
    }
  };

  const showMessage = (type, text) => {
    setMessage({ type, text });
    setTimeout(() => setMessage({ type: '', text: '' }), 5000);
  };

  return (
    <ThemeProvider theme={theme}>
      <AppBar position="static">
        <Toolbar>
          <Typography variant="h6" component="div" sx={{ flexGrow: 1 }}>
            Republic Services - Hazardous Waste Profiling
          </Typography>
          <Typography variant="body2">
            AI Agent Assist
          </Typography>
        </Toolbar>
      </AppBar>

      <Container maxWidth="xl" sx={{ mt: 4, mb: 4 }}>
        {message.text && (
          <Alert severity={message.type} sx={{ mb: 2 }}>
            {message.text}
          </Alert>
        )}

        <Paper sx={{ width: '100%' }}>
          <Tabs value={tabValue} onChange={(e, newValue) => setTabValue(newValue)}>
            <Tab label="Create Profile" />
            <Tab label="View Profiles" />
            <Tab label="AI Recommendations" />
          </Tabs>

          <TabPanel value={tabValue} index={0}>
            <ProfileForm onSubmit={handleProfileSubmit} loading={loading} />
          </TabPanel>

          <TabPanel value={tabValue} index={1}>
            <ProfileList profiles={profiles} loading={loading} onRefresh={loadProfiles} />
          </TabPanel>

          <TabPanel value={tabValue} index={2}>
            <AIRecommendations />
          </TabPanel>
        </Paper>
      </Container>
    </ThemeProvider>
  );
}

export default App;