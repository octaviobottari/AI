import React, { useState } from 'react';
import {
  Box,
  Button,
  TextField,
  Grid,
  Typography,
  MenuItem,
  Accordion,
  AccordionSummary,
  AccordionDetails,
  FormControl,
  InputLabel,
  Select,
  Chip,
  Alert
} from '@mui/material';
import ExpandMoreIcon from '@mui/icons-material/ExpandMore';
import AddIcon from '@mui/icons-material/Add';

const wasteCodes = ['D001', 'D002', 'D003', 'D004', 'F001', 'F006'];
const physicalStates = ['solid', 'liquid', 'gas', 'sludge', 'powder'];

const ProfileForm = ({ onSubmit, loading = false }) => {
  const [formData, setFormData] = useState({
    generator_info: {
      name: '',
      address: '',
      epa_id: '',
      contact_name: '',
      contact_phone: '',
      contact_email: ''
    },
    common_name: '',
    generating_process: '',
    physical_properties: {
      physical_state: '',
      physical_description: '',
      odor: '',
      color: '',
      ph: '',
      flash_point: '',
      flash_point_unit: '°F'
    },
    chemical_constituents: [{ name: '', concentration: '', cas_number: '', units: 'mg/kg' }],
    waste_codes: [],
    additional_properties: {}
  });

  const [errors, setErrors] = useState({});

  // Función corregida para campos normales
  const handleInputChange = (field, value) => {
    setFormData(prev => ({
      ...prev,
      [field]: value
    }));
  };

  // Función corregida para campos anidados
  const handleNestedInputChange = (section, field, value) => {
    setFormData(prev => ({
      ...prev,
      [section]: {
        ...prev[section],
        [field]: value
      }
    }));
  };

  // Función corregida para propiedades físicas
  const handlePhysicalPropertyChange = (field, value) => {
    setFormData(prev => ({
      ...prev,
      physical_properties: {
        ...prev.physical_properties,
        [field]: value
      }
    }));
  };

  const handleChemicalChange = (index, field, value) => {
    const updatedChemicals = formData.chemical_constituents.map((chem, i) =>
      i === index ? { ...chem, [field]: value } : chem
    );
    setFormData(prev => ({ ...prev, chemical_constituents: updatedChemicals }));
  };

  const addChemical = () => {
    setFormData(prev => ({
      ...prev,
      chemical_constituents: [
        ...prev.chemical_constituents,
        { name: '', concentration: '', cas_number: '', units: 'mg/kg' }
      ]
    }));
  };

  const removeChemical = (index) => {
    if (formData.chemical_constituents.length > 1) {
      const updatedChemicals = formData.chemical_constituents.filter((_, i) => i !== index);
      setFormData(prev => ({ ...prev, chemical_constituents: updatedChemicals }));
    }
  };

  // Validación corregida
  const validateForm = () => {
    const newErrors = {};
    
    // Validar campos requeridos con verificaciones de existencia
    if (!formData.generator_info?.name?.trim()) newErrors.generator_name = 'Generator name is required';
    if (!formData.generator_info?.address?.trim()) newErrors.generator_address = 'Address is required';
    if (!formData.generator_info?.contact_name?.trim()) newErrors.contact_name = 'Contact name is required';
    if (!formData.generator_info?.contact_phone?.trim()) newErrors.contact_phone = 'Contact phone is required';
    if (!formData.generator_info?.contact_email?.trim()) newErrors.contact_email = 'Contact email is required';
    if (!formData.common_name?.trim()) newErrors.common_name = 'Common name is required';
    if (!formData.generating_process?.trim()) newErrors.generating_process = 'Generating process is required';
    
    setErrors(newErrors);
    return Object.keys(newErrors).length === 0;
  };

  const handleSubmit = (e) => {
    e.preventDefault();
    if (validateForm()) {
      onSubmit(formData);
    }
  };

  return (
    <Box component="form" onSubmit={handleSubmit}>
      <Grid container spacing={3}>
        
        {/* Generator Information */}
        <Grid item xs={12}>
          <Accordion defaultExpanded>
            <AccordionSummary expandIcon={<ExpandMoreIcon />}>
              <Typography variant="h6">Generator Information</Typography>
            </AccordionSummary>
            <AccordionDetails>
              <Grid container spacing={2}>
                <Grid item xs={12} sm={6}>
                  <TextField
                    fullWidth
                    label="Generator Name *"
                    value={formData.generator_info.name || ''}
                    onChange={(e) => handleNestedInputChange('generator_info', 'name', e.target.value)}
                    error={!!errors.generator_name}
                    helperText={errors.generator_name}
                    required
                  />
                </Grid>
                <Grid item xs={12} sm={6}>
                  <TextField
                    fullWidth
                    label="EPA ID"
                    value={formData.generator_info.epa_id || ''}
                    onChange={(e) => handleNestedInputChange('generator_info', 'epa_id', e.target.value)}
                  />
                </Grid>
                <Grid item xs={12}>
                  <TextField
                    fullWidth
                    label="Address *"
                    value={formData.generator_info.address || ''}
                    onChange={(e) => handleNestedInputChange('generator_info', 'address', e.target.value)}
                    error={!!errors.generator_address}
                    helperText={errors.generator_address}
                    required
                  />
                </Grid>
                <Grid item xs={12} sm={4}>
                  <TextField
                    fullWidth
                    label="Contact Name *"
                    value={formData.generator_info.contact_name || ''}
                    onChange={(e) => handleNestedInputChange('generator_info', 'contact_name', e.target.value)}
                    error={!!errors.contact_name}
                    helperText={errors.contact_name}
                    required
                  />
                </Grid>
                <Grid item xs={12} sm={4}>
                  <TextField
                    fullWidth
                    label="Contact Phone *"
                    value={formData.generator_info.contact_phone || ''}
                    onChange={(e) => handleNestedInputChange('generator_info', 'contact_phone', e.target.value)}
                    error={!!errors.contact_phone}
                    helperText={errors.contact_phone}
                    required
                  />
                </Grid>
                <Grid item xs={12} sm={4}>
                  <TextField
                    fullWidth
                    label="Contact Email *"
                    type="email"
                    value={formData.generator_info.contact_email || ''}
                    onChange={(e) => handleNestedInputChange('generator_info', 'contact_email', e.target.value)}
                    error={!!errors.contact_email}
                    helperText={errors.contact_email}
                    required
                  />
                </Grid>
              </Grid>
            </AccordionDetails>
          </Accordion>
        </Grid>

        {/* Waste Basic Information */}
        <Grid item xs={12}>
          <Accordion defaultExpanded>
            <AccordionSummary expandIcon={<ExpandMoreIcon />}>
              <Typography variant="h6">Waste Basic Information</Typography>
            </AccordionSummary>
            <AccordionDetails>
              <Grid container spacing={2}>
                <Grid item xs={12} sm={6}>
                  <TextField
                    fullWidth
                    label="Common Name *"
                    value={formData.common_name || ''}
                    onChange={(e) => handleInputChange('common_name', e.target.value)}
                    error={!!errors.common_name}
                    helperText={errors.common_name}
                    required
                  />
                </Grid>
                <Grid item xs={12} sm={6}>
                  <TextField
                    fullWidth
                    label="Generating Process *"
                    value={formData.generating_process || ''}
                    onChange={(e) => handleInputChange('generating_process', e.target.value)}
                    error={!!errors.generating_process}
                    helperText={errors.generating_process}
                    required
                  />
                </Grid>
                <Grid item xs={12}>
                  <FormControl fullWidth>
                    <InputLabel>Waste Codes</InputLabel>
                    <Select
                      multiple
                      value={formData.waste_codes}
                      onChange={(e) => handleInputChange('waste_codes', e.target.value)}
                      renderValue={(selected) => (
                        <Box sx={{ display: 'flex', flexWrap: 'wrap', gap: 0.5 }}>
                          {selected.map((value) => (
                            <Chip key={value} label={value} />
                          ))}
                        </Box>
                      )}
                    >
                      {wasteCodes.map((code) => (
                        <MenuItem key={code} value={code}>
                          {code}
                        </MenuItem>
                      ))}
                    </Select>
                  </FormControl>
                </Grid>
              </Grid>
            </AccordionDetails>
          </Accordion>
        </Grid>

        {/* Physical Properties - CORREGIDO */}
        <Grid item xs={12}>
          <Accordion>
            <AccordionSummary expandIcon={<ExpandMoreIcon />}>
              <Typography variant="h6">Physical Properties</Typography>
            </AccordionSummary>
            <AccordionDetails>
              <Grid container spacing={2}>
                <Grid item xs={12} sm={4}>
                  <FormControl fullWidth>
                    <InputLabel>Physical State</InputLabel>
                    <Select
                      value={formData.physical_properties.physical_state || ''}
                      onChange={(e) => handlePhysicalPropertyChange('physical_state', e.target.value)}
                      label="Physical State"
                    >
                      {physicalStates.map((state) => (
                        <MenuItem key={state} value={state}>
                          {state}
                        </MenuItem>
                      ))}
                    </Select>
                  </FormControl>
                </Grid>
                <Grid item xs={12} sm={8}>
                  <TextField
                    fullWidth
                    label="Physical Description"
                    value={formData.physical_properties.physical_description || ''}
                    onChange={(e) => handlePhysicalPropertyChange('physical_description', e.target.value)}
                  />
                </Grid>
                <Grid item xs={12} sm={4}>
                  <TextField
                    fullWidth
                    label="Odor"
                    value={formData.physical_properties.odor || ''}
                    onChange={(e) => handlePhysicalPropertyChange('odor', e.target.value)}
                  />
                </Grid>
                <Grid item xs={12} sm={4}>
                  <TextField
                    fullWidth
                    label="Color"
                    value={formData.physical_properties.color || ''}
                    onChange={(e) => handlePhysicalPropertyChange('color', e.target.value)}
                  />
                </Grid>
                <Grid item xs={12} sm={4}>
                  <TextField
                    fullWidth
                    label="pH"
                    type="number"
                    value={formData.physical_properties.ph || ''}
                    onChange={(e) => handlePhysicalPropertyChange('ph', e.target.value)}
                  />
                </Grid>
                <Grid item xs={12} sm={6}>
                  <TextField
                    fullWidth
                    label="Flash Point (°F)"
                    type="number"
                    value={formData.physical_properties.flash_point || ''}
                    onChange={(e) => handlePhysicalPropertyChange('flash_point', e.target.value)}
                  />
                </Grid>
              </Grid>
            </AccordionDetails>
          </Accordion>
        </Grid>

        {/* Chemical Constituents */}
        <Grid item xs={12}>
          <Accordion>
            <AccordionSummary expandIcon={<ExpandMoreIcon />}>
              <Typography variant="h6">Chemical Constituents</Typography>
            </AccordionSummary>
            <AccordionDetails>
              {formData.chemical_constituents.map((chemical, index) => (
                <Grid container spacing={2} key={index} sx={{ mb: 2, p: 2, border: '1px solid #ddd', borderRadius: 1 }}>
                  <Grid item xs={12} sm={4}>
                    <TextField
                      fullWidth
                      label="Chemical Name"
                      value={chemical.name || ''}
                      onChange={(e) => handleChemicalChange(index, 'name', e.target.value)}
                    />
                  </Grid>
                  <Grid item xs={12} sm={3}>
                    <TextField
                      fullWidth
                      label="Concentration"
                      type="number"
                      value={chemical.concentration || ''}
                      onChange={(e) => handleChemicalChange(index, 'concentration', e.target.value)}
                    />
                  </Grid>
                  <Grid item xs={12} sm={3}>
                    <TextField
                      fullWidth
                      label="CAS Number"
                      value={chemical.cas_number || ''}
                      onChange={(e) => handleChemicalChange(index, 'cas_number', e.target.value)}
                    />
                  </Grid>
                  <Grid item xs={12} sm={2}>
                    <TextField
                      fullWidth
                      label="Units"
                      value={chemical.units || ''}
                      onChange={(e) => handleChemicalChange(index, 'units', e.target.value)}
                    />
                  </Grid>
                  {formData.chemical_constituents.length > 1 && (
                    <Grid item xs={12}>
                      <Button 
                        color="error" 
                        onClick={() => removeChemical(index)}
                        size="small"
                      >
                        Remove
                      </Button>
                    </Grid>
                  )}
                </Grid>
              ))}
              <Button startIcon={<AddIcon />} onClick={addChemical} variant="outlined">
                Add Chemical
              </Button>
            </AccordionDetails>
          </Accordion>
        </Grid>

        {/* Submit Button */}
        <Grid item xs={12}>
          <Box sx={{ display: 'flex', justifyContent: 'flex-end', gap: 2 }}>
            <Button 
              type="submit" 
              variant="contained" 
              size="large"
              disabled={loading}
            >
              {loading ? 'Creating Profile...' : 'Create Profile & Validate with AI'}
            </Button>
          </Box>
        </Grid>
      </Grid>
    </Box>
  );
};

export default ProfileForm;