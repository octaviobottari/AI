#!/bin/bash
echo "🚀 Setting up Hazardous Waste Profiling System..."

# Backend setup
echo "📦 Setting up backend..."
cd backend
python3 -m venv venv
source venv/bin/activate

# Check if requirements.txt exists, if not create it
if [ ! -f requirements.txt ]; then
    echo "Creating requirements.txt..."
    cat > requirements.txt << EOL
fastapi==0.104.1
uvicorn==0.24.0
pydantic==2.5.0
boto3==1.34.0
python-multipart==0.0.6
EOL
fi

pip install -r requirements.txt

# Initialize database
echo "🗃️ Initializing database..."
python3 -c "
from main import init_db
init_db()
print('✅ Database initialized')
"

# Frontend setup
echo "📦 Setting up frontend..."
cd ../frontend

# Check if package.json exists, if not create it
if [ ! -f package.json ]; then
    echo "Creating package.json..."
    cat > package.json << EOL
{
  "name": "hazardous-waste-profiler-frontend",
  "version": "1.0.0",
  "type": "module",
  "dependencies": {
    "@mui/material": "^5.14.0",
    "@emotion/react": "^11.11.0",
    "@emotion/styled": "^11.11.0",
    "@mui/icons-material": "^5.14.0",
    "react": "^18.2.0",
    "react-dom": "^18.2.0",
    "react-scripts": "5.0.1"
  },
  "scripts": {
    "start": "react-scripts start",
    "build": "react-scripts build",
    "test": "react-scripts test",
    "eject": "react-scripts eject"
  }
}
EOL
fi

npm install

echo ""
echo "✅ Setup complete!"
echo ""
echo "🎯 To start the application:"
echo "   1. Start Backend: cd backend && source venv/bin/activate && python main.py"
echo "   2. Start Frontend: cd frontend && npm start"
echo ""
echo "📱 Access the application at: http://localhost:3000"
echo "🔧 Backend API running at: http://localhost:8000"