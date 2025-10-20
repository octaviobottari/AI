# backend/main.py
from fastapi import FastAPI, HTTPException, Depends, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any
from datetime import datetime
import boto3
import json
import uuid
from enum import Enum
import sqlite3
import os
from contextlib import contextmanager
import logging

# Configurar logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(title="Hazardous Waste Profile AI Agent", version="1.0.0")

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://127.0.0.1:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Database setup
DATABASE_URL = "sqlite:///profiles.db"

class ProfileStatus(str, Enum):
    DRAFT = "draft"
    SUBMITTED = "submitted"
    APPROVED = "approved"
    REJECTED = "rejected"
    CORRECTION_NEEDED = "correction_needed"

class WasteCode(str, Enum):
    D001 = "D001"  # Ignitable
    D002 = "D002"  # Corrosive
    D003 = "D003"  # Reactive
    D004 = "D004"  # Toxic
    F001 = "F001"  # Spent solvents
    F006 = "F006"  # Wastewater treatment sludges

class PhysicalState(str, Enum):
    SOLID = "solid"
    LIQUID = "liquid"
    GAS = "gas"
    SLUDGE = "sludge"
    POWDER = "powder"

# Pydantic models
class ChemicalConstituent(BaseModel):
    name: str
    concentration: float
    cas_number: Optional[str] = None
    units: str = "mg/kg"

class GeneratorInfo(BaseModel):
    name: str
    address: str
    epa_id: Optional[str] = None
    contact_name: str
    contact_phone: str
    contact_email: str

class PhysicalProperties(BaseModel):
    physical_state: PhysicalState
    physical_description: str
    odor: Optional[str] = None
    color: Optional[str] = None
    ph: Optional[float] = None
    flash_point: Optional[float] = None  # °F
    flash_point_unit: str = "°F"

class WasteProfileCreate(BaseModel):
    generator_info: GeneratorInfo
    common_name: str
    generating_process: str
    physical_properties: PhysicalProperties
    chemical_constituents: List[ChemicalConstituent]
    waste_codes: List[WasteCode]
    additional_properties: Dict[str, Any] = {}
    facility_id: Optional[str] = None

class AIRecommendation(BaseModel):
    field_name: str
    current_value: Any
    recommended_value: Any
    reasoning: str
    confidence: float
    is_correct: Optional[bool] = None

class WasteProfileResponse(BaseModel):
    id: str
    generator_info: GeneratorInfo
    common_name: str
    generating_process: str
    physical_properties: PhysicalProperties
    chemical_constituents: List[ChemicalConstituent]
    waste_codes: List[WasteCode]
    additional_properties: Dict[str, Any]
    facility_id: Optional[str] = None
    status: ProfileStatus
    ai_recommendations: List[AIRecommendation] = []
    submission_date: datetime
    last_modified: datetime

class ProfileValidationRequest(BaseModel):
    profile_data: Dict[str, Any]

# Database setup
@contextmanager
def get_db():
    conn = sqlite3.connect('profiles.db')
    conn.row_factory = sqlite3.Row
    try:
        yield conn
    finally:
        conn.close()

def init_db():
    with get_db() as conn:
        conn.execute('''
            CREATE TABLE IF NOT EXISTS waste_profiles (
                id TEXT PRIMARY KEY,
                generator_info TEXT,
                common_name TEXT,
                generating_process TEXT,
                physical_properties TEXT,
                chemical_constituents TEXT,
                waste_codes TEXT,
                additional_properties TEXT,
                facility_id TEXT,
                status TEXT,
                submission_date TEXT,
                last_modified TEXT
            )
        ''')
        
        conn.execute('''
            CREATE TABLE IF NOT EXISTS ai_recommendations (
                id TEXT PRIMARY KEY,
                profile_id TEXT,
                field_name TEXT,
                current_value TEXT,
                recommended_value TEXT,
                reasoning TEXT,
                confidence REAL,
                is_correct BOOLEAN,
                created_date TEXT,
                FOREIGN KEY (profile_id) REFERENCES waste_profiles (id)
            )
        ''')
        
        conn.execute('''
            CREATE TABLE IF NOT EXISTS recommendation_history (
                id TEXT PRIMARY KEY,
                profile_id TEXT,
                action TEXT,
                user_id TEXT,
                timestamp TEXT,
                details TEXT,
                FOREIGN KEY (profile_id) REFERENCES waste_profiles (id)
            )
        ''')

# AI Service - CORREGIDO
class AIService:
    def __init__(self):
        try:
            # Usar tu región actual (us-east-1)
            self.region = 'us-east-1'
            self.bedrock_runtime = boto3.client('bedrock-runtime', region_name=self.region)
            self.bedrock = boto3.client('bedrock', region_name=self.region)  # Cliente para listar modelos
            
            # Lista de modelos a probar
            self.available_models = [
                "amazon.titan-text-express-v1",
                "anthropic.claude-3-5-sonnet-20240620-v1:0", 
                "meta.llama3-1-8b-instruct-v1:0",
                "meta.llama3-1-70b-instruct-v1:0"
            ]
            
            self.model_id = self._get_available_model()
            
        except Exception as e:
            logger.error(f"❌ Failed to initialize AI service: {e}")
            self.bedrock_runtime = None
            self.bedrock = None
            self.model_id = None
    
    def _get_available_model(self):
        """Get first available model from the list"""
        try:
            # Obtener modelos disponibles usando el cliente bedrock (no bedrock-runtime)
            available_models_response = self.bedrock.list_foundation_models()
            available_model_ids = [model['modelId'] for model in available_models_response['modelSummaries']]
            
            logger.info(f"📋 Available models in {self.region}: {available_model_ids}")
            
            # Buscar el primer modelo de nuestra lista que esté disponible
            for model_id in self.available_models:
                if model_id in available_model_ids:
                    logger.info(f"✅ Using AI model: {model_id}")
                    return model_id
            
            logger.warning("⚠️ No preferred models available, trying direct access...")
            
            # Si no encontramos modelos preferidos, probar acceso directo
            for model_id in self.available_models:
                try:
                    # Probar invocación simple
                    if "titan" in model_id:
                        test_body = {"inputText": "test", "textGenerationConfig": {"maxTokenCount": 5}}
                    elif "claude" in model_id:
                        test_body = {"anthropic_version": "bedrock-2023-05-31", "max_tokens": 5, "messages": [{"role": "user", "content": "test"}]}
                    else:  # llama
                        test_body = {"prompt": "test", "max_gen_len": 5}
                    
                    self.bedrock_runtime.invoke_model(
                        modelId=model_id,
                        body=json.dumps(test_body)
                    )
                    logger.info(f"✅ Model {model_id} is accessible")
                    return model_id
                    
                except Exception as e:
                    logger.warning(f"❌ Model {model_id} not accessible: {e}")
                    continue
            
            logger.warning("⚠️ No AI models available, using fallback mode")
            return None
            
        except Exception as e:
            logger.error(f"❌ Error checking available models: {e}")
            return None
    
    def generate_recommendations(self, profile_data: Dict[str, Any]) -> List[AIRecommendation]:
        """Generate AI recommendations for profile validation"""
        
        logger.info("🔧 Attempting to generate AI recommendations...")
        
        # Si no hay servicio de AI disponible, usar fallback
        if not self.bedrock_runtime or not self.model_id:
            logger.info("🔄 Using fallback recommendations (no AI service)")
            return self._get_fallback_recommendations(profile_data)
        
        prompt = self._build_validation_prompt(profile_data)
        
        try:
            logger.info(f"🤖 Sending request to {self.model_id}...")
            
            # Configuración específica por modelo
            if "claude" in self.model_id:
                body = {
                    "anthropic_version": "bedrock-2023-05-31",
                    "max_tokens": 1000,
                    "temperature": 0.1,
                    "messages": [{
                        "role": "user",
                        "content": prompt
                    }]
                }
            elif "llama" in self.model_id:
                body = {
                    "prompt": prompt,
                    "max_gen_len": 1024,
                    "temperature": 0.1,
                    "top_p": 0.9
                }
            else:  # Titan y otros
                body = {
                    "inputText": prompt,
                    "textGenerationConfig": {
                        "maxTokenCount": 1024,
                        "temperature": 0.1,
                        "topP": 0.9
                    }
                }
            
            response = self.bedrock_runtime.invoke_model(
                modelId=self.model_id,
                body=json.dumps(body)
            )
            
            logger.info("✅ Received response from AI")
            response_body = json.loads(response['body'].read())
            
            # Parsear respuesta según el modelo
            if "claude" in self.model_id:
                recommendations_text = response_body['content'][0]['text']
            elif "llama" in self.model_id:
                recommendations_text = response_body['generation']
            else:  # Titan
                recommendations_text = response_body['results'][0]['outputText']
            
            logger.info(f"📝 AI Response: {recommendations_text[:500]}...")
            
            return self._parse_recommendations(recommendations_text, profile_data)
            
        except Exception as e:
            logger.error(f"❌ AI service error: {e}")
            logger.info("🔄 Using fallback recommendations")
            return self._get_fallback_recommendations(profile_data)
    
    def _build_validation_prompt(self, profile_data: Dict[str, Any]) -> str:
        """Build prompt for AI validation"""
        
        return f"""
Eres un experto en perfiles de residuos peligrosos. Analiza este perfil y proporciona recomendaciones de validación.

DATOS DEL PERFIL:
{json.dumps(profile_data, indent=2, ensure_ascii=False)}

REGLAS:
1. Verificar campos obligatorios faltantes
2. Validar concentraciones de constituyentes químicos contra límites regulatorios
3. Verificar asignaciones de códigos de residuo basadas en propiedades y constituyentes
4. Verificar consistencia de propiedades físicas
5. Validar completitud de información del generador

Proporciona recomendaciones en este formato JSON exacto:
{{
    "recommendations": [
        {{
            "field_name": "nombre_del_campo",
            "current_value": "valor_actual",
            "recommended_value": "valor_recomendado", 
            "reasoning": "explicación_detallada",
            "confidence": 0.95
        }}
    ]
}}

Enfócate en problemas críticos que causarían rechazo. Sé específico y accionable.
"""
    
    def _parse_recommendations(self, text: str, profile_data: Dict[str, Any]) -> List[AIRecommendation]:
        """Parse AI response into structured recommendations"""
        try:
            logger.info(f"📝 Parsing AI response...")
            
            # Extract JSON from response
            start_idx = text.find('{')
            end_idx = text.rfind('}') + 1
            
            if start_idx == -1 or end_idx == 0:
                logger.warning("❌ No JSON found in AI response")
                return self._get_fallback_recommendations(profile_data)
                
            json_str = text[start_idx:end_idx]
            data = json.loads(json_str)
            
            recommendations = []
            for rec in data.get('recommendations', []):
                recommendations.append(AIRecommendation(**rec))
            
            logger.info(f"✅ Successfully parsed {len(recommendations)} recommendations")
            return recommendations
            
        except Exception as e:
            logger.error(f"❌ Error parsing AI recommendations: {e}")
            return self._get_fallback_recommendations(profile_data)
    
    def _get_fallback_recommendations(self, profile_data: Dict[str, Any]) -> List[AIRecommendation]:
        """Provide basic rule-based recommendations when AI fails"""
        logger.info("🔄 Generating fallback recommendations")
        recommendations = []
        
        # Basic validation rules
        generator_info = profile_data.get('generator_info', {})
        physical_props = profile_data.get('physical_properties', {})
        chemical_constituents = profile_data.get('chemical_constituents', [])
        
        # Check EPA ID
        if not generator_info.get('epa_id'):
            recommendations.append(
                AIRecommendation(
                    field_name="generator_info.epa_id",
                    current_value="",
                    recommended_value="Required EPA ID",
                    reasoning="Generator EPA ID is required for hazardous waste profiling",
                    confidence=0.95
                )
            )
        
        # Check for extreme pH values
        if physical_props.get('ph'):
            ph_value = physical_props['ph']
            if ph_value < 2 or ph_value > 12.5:
                recommendations.append(
                    AIRecommendation(
                        field_name="physical_properties.ph",
                        current_value=ph_value,
                        recommended_value=f"Verify extreme pH value ({ph_value})",
                        reasoning="Extreme pH values may indicate measurement error or require special handling",
                        confidence=0.8
                    )
                )
        
        # Check chemical concentrations
        for i, chem in enumerate(chemical_constituents):
            if chem.get('concentration') and chem['concentration'] > 1000:
                recommendations.append(
                    AIRecommendation(
                        field_name=f"chemical_constituents[{i}].concentration",
                        current_value=chem['concentration'],
                        recommended_value="Verify high concentration",
                        reasoning=f"High concentration of {chem.get('name', 'unknown chemical')} may require special handling",
                        confidence=0.7
                    )
                )
        
        # Check waste codes assignment
        waste_codes = profile_data.get('waste_codes', [])
        if not waste_codes and chemical_constituents:
            recommendations.append(
                AIRecommendation(
                    field_name="waste_codes",
                    current_value="None assigned",
                    recommended_value="Assign appropriate waste codes",
                    reasoning="Waste codes should be assigned based on chemical constituents and properties",
                    confidence=0.9
                )
            )
        
        logger.info(f"🔄 Generated {len(recommendations)} fallback recommendations")
        return recommendations

# Initialize services
ai_service = AIService()

# Simple routes for testing
@app.get("/")
def read_root():
    return {"message": "Hazardous Waste Profiling API is running!"}

@app.get("/health")
def health_check():
    ai_status = "available" if ai_service.bedrock_runtime and ai_service.model_id else "fallback"
    return {
        "status": "healthy", 
        "timestamp": datetime.utcnow().isoformat(),
        "ai_status": ai_status,
        "ai_model": ai_service.model_id,
        "region": ai_service.region if ai_service else "unknown"
    }

# Debug endpoint
@app.get("/debug/profiles")
async def debug_profiles():
    """Debug endpoint to check profiles and AI recommendations"""
    with get_db() as conn:
        profile_rows = conn.execute('SELECT id, common_name, status FROM waste_profiles').fetchall()
        profiles_info = []
        
        for profile_row in profile_rows:
            recommendation_count = conn.execute(
                'SELECT COUNT(*) as count FROM ai_recommendations WHERE profile_id = ?', 
                (profile_row['id'],)
            ).fetchone()['count']
            
            profiles_info.append({
                'id': profile_row['id'],
                'common_name': profile_row['common_name'],
                'status': profile_row['status'],
                'ai_recommendations_count': recommendation_count
            })
    
    return {
        "total_profiles": len(profiles_info),
        "profiles": profiles_info
    }

# API Routes
@app.post("/profiles", response_model=WasteProfileResponse)
async def create_profile(profile: WasteProfileCreate, background_tasks: BackgroundTasks):
    """Create a new waste profile and trigger AI validation"""
    profile_id = str(uuid.uuid4())
    now = datetime.utcnow().isoformat()
    
    profile_dict = profile.dict()
    profile_dict['id'] = profile_id
    profile_dict['status'] = ProfileStatus.DRAFT
    profile_dict['submission_date'] = now
    profile_dict['last_modified'] = now
    
    logger.info(f"🎯 Creating new profile: {profile_dict['common_name']}")
    
    # Store in database
    with get_db() as conn:
        conn.execute('''
            INSERT INTO waste_profiles 
            (id, generator_info, common_name, generating_process, physical_properties, 
             chemical_constituents, waste_codes, additional_properties, facility_id, status, submission_date, last_modified)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (
            profile_id,
            json.dumps(profile_dict['generator_info']),
            profile_dict['common_name'],
            profile_dict['generating_process'],
            json.dumps(profile_dict['physical_properties']),
            json.dumps(profile_dict['chemical_constituents']),
            json.dumps(profile_dict['waste_codes']),
            json.dumps(profile_dict['additional_properties']),
            profile_dict.get('facility_id'),
            profile_dict['status'].value,
            profile_dict['submission_date'],
            profile_dict['last_modified']
        ))
        conn.commit()
    
    # Trigger AI validation in background
    logger.info(f"🚀 Adding background task for AI validation on profile {profile_id}")
    background_tasks.add_task(generate_ai_recommendations, profile_id, profile_dict)
    
    logger.info(f"✅ Profile {profile_id} created successfully")
    return WasteProfileResponse(**profile_dict)

@app.get("/profiles", response_model=List[WasteProfileResponse])
async def get_all_profiles():
    """Get all waste profiles"""
    with get_db() as conn:
        profile_rows = conn.execute('SELECT * FROM waste_profiles').fetchall()
        
        profiles = []
        for profile_row in profile_rows:
            # Get AI recommendations for each profile
            recommendation_rows = conn.execute(
                'SELECT * FROM ai_recommendations WHERE profile_id = ?', (profile_row['id'],)
            ).fetchall()
            
            profile_data = {
                'id': profile_row['id'],
                'generator_info': json.loads(profile_row['generator_info']),
                'common_name': profile_row['common_name'],
                'generating_process': profile_row['generating_process'],
                'physical_properties': json.loads(profile_row['physical_properties']),
                'chemical_constituents': json.loads(profile_row['chemical_constituents']),
                'waste_codes': json.loads(profile_row['waste_codes']),
                'additional_properties': json.loads(profile_row['additional_properties']),
                'facility_id': profile_row['facility_id'],
                'status': ProfileStatus(profile_row['status']),
                'submission_date': datetime.fromisoformat(profile_row['submission_date']),
                'last_modified': datetime.fromisoformat(profile_row['last_modified']),
                'ai_recommendations': []
            }
            
            for rec_row in recommendation_rows:
                profile_data['ai_recommendations'].append({
                    'field_name': rec_row['field_name'],
                    'current_value': rec_row['current_value'],
                    'recommended_value': rec_row['recommended_value'],
                    'reasoning': rec_row['reasoning'],
                    'confidence': rec_row['confidence'],
                    'is_correct': bool(rec_row['is_correct']) if rec_row['is_correct'] is not None else None
                })
            
            profiles.append(profile_data)
    
    return profiles

@app.get("/profiles/{profile_id}", response_model=WasteProfileResponse)
async def get_profile(profile_id: str):
    """Get a specific waste profile"""
    with get_db() as conn:
        profile_row = conn.execute(
            'SELECT * FROM waste_profiles WHERE id = ?', (profile_id,)
        ).fetchone()
        
        if not profile_row:
            raise HTTPException(status_code=404, detail="Profile not found")
        
        # Get AI recommendations
        recommendation_rows = conn.execute(
            'SELECT * FROM ai_recommendations WHERE profile_id = ?', (profile_id,)
        ).fetchall()
    
    profile_data = {
        'id': profile_row['id'],
        'generator_info': json.loads(profile_row['generator_info']),
        'common_name': profile_row['common_name'],
        'generating_process': profile_row['generating_process'],
        'physical_properties': json.loads(profile_row['physical_properties']),
        'chemical_constituents': json.loads(profile_row['chemical_constituents']),
        'waste_codes': json.loads(profile_row['waste_codes']),
        'additional_properties': json.loads(profile_row['additional_properties']),
        'facility_id': profile_row['facility_id'],
        'status': ProfileStatus(profile_row['status']),
        'submission_date': datetime.fromisoformat(profile_row['submission_date']),
        'last_modified': datetime.fromisoformat(profile_row['last_modified']),
        'ai_recommendations': []
    }
    
    for rec_row in recommendation_rows:
        profile_data['ai_recommendations'].append({
            'field_name': rec_row['field_name'],
            'current_value': rec_row['current_value'],
            'recommended_value': rec_row['recommended_value'],
            'reasoning': rec_row['reasoning'],
            'confidence': rec_row['confidence'],
            'is_correct': bool(rec_row['is_correct']) if rec_row['is_correct'] is not None else None
        })
    
    return WasteProfileResponse(**profile_data)

@app.post("/profiles/{profile_id}/validate")
async def validate_profile(profile_id: str):
    """Trigger AI validation for an existing profile"""
    with get_db() as conn:
        profile_row = conn.execute(
            'SELECT * FROM waste_profiles WHERE id = ?', (profile_id,)
        ).fetchone()
        
        if not profile_row:
            raise HTTPException(status_code=404, detail="Profile not found")
    
    profile_data = {
        'generator_info': json.loads(profile_row['generator_info']),
        'common_name': profile_row['common_name'],
        'generating_process': profile_row['generating_process'],
        'physical_properties': json.loads(profile_row['physical_properties']),
        'chemical_constituents': json.loads(profile_row['chemical_constituents']),
        'waste_codes': json.loads(profile_row['waste_codes']),
        'additional_properties': json.loads(profile_row['additional_properties'])
    }
    
    recommendations = generate_ai_recommendations(profile_id, profile_data)
    
    return {"message": "Validation completed", "recommendations_count": len(recommendations)}

@app.post("/profiles/{profile_id}/recommendations/{recommendation_id}/feedback")
async def submit_feedback(profile_id: str, recommendation_id: str, feedback: bool):
    """Submit feedback on AI recommendation accuracy"""
    with get_db() as conn:
        conn.execute(
            'UPDATE ai_recommendations SET is_correct = ? WHERE id = ? AND profile_id = ?',
            (feedback, recommendation_id, profile_id)
        )
        
        # Log feedback in history
        history_id = str(uuid.uuid4())
        conn.execute('''
            INSERT INTO recommendation_history (id, profile_id, action, user_id, timestamp, details)
            VALUES (?, ?, ?, ?, ?, ?)
        ''', (
            history_id,
            profile_id,
            'feedback',
            'user',
            datetime.utcnow().isoformat(),
            json.dumps({
                'recommendation_id': recommendation_id,
                'feedback': feedback
            })
        ))
        conn.commit()
    
    return {"message": "Feedback submitted successfully"}

# Background task
def generate_ai_recommendations(profile_id: str, profile_data: Dict[str, Any]):
    """Generate and store AI recommendations for a profile"""
    logger.info(f"🎯 Starting AI validation for profile {profile_id}")
    
    try:
        recommendations = ai_service.generate_recommendations(profile_data)
        logger.info(f"✅ AI generated {len(recommendations)} recommendations for profile {profile_id}")
        
        with get_db() as conn:
            # Clear existing recommendations
            conn.execute('DELETE FROM ai_recommendations WHERE profile_id = ?', (profile_id,))
            
            # Store new recommendations
            for rec in recommendations:
                rec_id = str(uuid.uuid4())
                conn.execute('''
                    INSERT INTO ai_recommendations 
                    (id, profile_id, field_name, current_value, recommended_value, reasoning, confidence, created_date)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                ''', (
                    rec_id,
                    profile_id,
                    rec.field_name,
                    str(rec.current_value),
                    str(rec.recommended_value),
                    rec.reasoning,
                    rec.confidence,
                    datetime.utcnow().isoformat()
                ))
            
            # Log generation in history
            history_id = str(uuid.uuid4())
            conn.execute('''
                INSERT INTO recommendation_history (id, profile_id, action, user_id, timestamp, details)
                VALUES (?, ?, ?, ?, ?, ?)
            ''', (
                history_id,
                profile_id,
                'recommendation_generated',
                'system',
                datetime.utcnow().isoformat(),
                json.dumps({'count': len(recommendations)})
            ))
            
            conn.commit()
        
        logger.info(f"💾 Saved {len(recommendations)} AI recommendations to database for profile {profile_id}")
        
    except Exception as e:
        logger.error(f"❌ Error in AI background task for profile {profile_id}: {e}")
    
    return recommendations

# Initialize database on startup
@app.on_event("startup")
async def startup_event():
    init_db()
    logger.info("✅ Database initialized")
    logger.info("🚀 Hazardous Waste Profiling API started")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000, log_level="info")