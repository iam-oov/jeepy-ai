#!/bin/bash
# Jeepy AI - Quick Start Script

echo "╔════════════════════════════════════════╗"
echo "║  🎙️  JEEPY AI - SCREAM ARCHITECTURE    ║"
echo "╚════════════════════════════════════════╝"
echo ""

# Colors
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Check if Python is installed
if ! command -v python3 &> /dev/null; then
    echo -e "${RED}❌ Python3 no está instalado${NC}"
    exit 1
fi

echo -e "${BLUE}📌 Verificando dependencias...${NC}"

# Check if virtual env exists
if [ ! -d "venv" ]; then
    echo -e "${YELLOW}📦 Creando entorno virtual...${NC}"
    python3 -m venv venv
fi

# Activate virtual env
source venv/bin/activate

# Install dependencies
echo -e "${YELLOW}📦 Instalando dependencias...${NC}"
pip install -q -r requirements.txt 2>/dev/null || {
    echo -e "${YELLOW}⚠️  Instalando manualmente...${NC}"
    pip install -q pyaudio numpy librosa tensorflow-lite google-genai openai psutil python-dotenv
}

echo ""
echo -e "${GREEN}✅ Ambiente listo!${NC}"
echo ""
echo -e "${BLUE}📚 Documentación:${NC}"
echo "   1. SCREAM_ARCHITECTURE.md - Guía completa"
echo "   2. SCREAM_VISUAL.md - Diagramas visuales"
echo "   3. README_SCREAM.md - Quick start"
echo "   4. MIGRATION_GUIDE.md - Cómo desarrollar"
echo ""
echo -e "${BLUE}🚀 Para ejecutar:${NC}"
echo "   python -m jeepy_ai.main"
echo ""
echo -e "${BLUE}📝 Para ver logs:${NC}"
echo "   tail -f jeepy_ai_monitor.log"
echo ""
