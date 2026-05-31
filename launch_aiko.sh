#!/bin/bash
# ╔══════════════════════════════════════════════════════════════╗
# ║                  PROJECT AIKO UNIX LAUNCHER                  ║
# ║           Warm up neural links, ignition & launch            ║
# ╚══════════════════════════════════════════════════════════════╝
# Usage: chmod +x launch_aiko.sh && ./launch_aiko.sh

set -e

# ANSI Color Codes
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
MAGENTA='\033[0;35m'
CYAN='\033[0;36m'
BOLD='\033[1m'
DIM='\033[2m'
NC='\033[0m' # No Color

print_banner() {
    clear
    echo -e "${MAGENTA}┏━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┓${NC}"
    echo -e "${MAGENTA}┃${NC} ${BOLD}         AIKO DESKTOP - NEURAL LINK LAUNCHER             ${NC} ${MAGENTA}┃${NC}"
    echo -e "${MAGENTA}┗━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┛${NC}"
    echo
}

print_banner

# -- 1. OS Info & Shell Diagnostics ---------------------------------
OS_TYPE=$(uname)
echo -e " ${BLUE}ℹ${NC} Operating System detected: ${BOLD}${OS_TYPE}${NC}"

# -- 2. Check for Python 3 ------------------------------------------
if ! command -v python3 &> /dev/null; then
    echo -e " ${RED}✘${NC} ${BOLD}[ERROR] Python 3 is not installed!${NC}"
    echo -e "   Please install Python 3.9+ using your package manager."
    echo -e "   For Debian/Ubuntu: sudo apt install python3 python3-venv"
    echo -e "   For macOS: brew install python"
    echo
    exit 1
fi

PYVER=$(python3 --version)
echo -e " ${GREEN}✓${NC} ${PYVER}"

# -- 3. Check for Node.js & npm ------------------------------------
HAS_NODE=0
if ! command -v node &> /dev/null; then
    echo -e " ${YELLOW}⚠${NC} ${DIM}Node.js not found.${NC}"
    echo -e "   Aiko will run in browser-fallback mode."
else
    HAS_NODE=1
    NODEVER=$(node --version)
    echo -e " ${GREEN}✓${NC} Node.js ${NODEVER}"
fi

# -- 4. Create Virtual Environment if needed ------------------------
if [ ! -f ".venv/bin/activate" ]; then
    echo
    echo -e " ${BLUE}ℹ${NC} Creating virtual environment [first time only]..."
    python3 -m venv .venv
    if [ $? -ne 0 ]; then
        echo -e " ${RED}✘${NC} ${BOLD}[ERROR] Failed to create virtual environment.${NC}"
        exit 1
    fi
    echo -e " ${GREEN}✓${NC} Virtual environment created."
fi

# -- 5. Activate environment ---------------------------------------
echo -e " ${BLUE}ℹ${NC} Warming up neural modules..."
source .venv/bin/activate

# -- 5a. First Run Setup (copy example files) -----------------------
if [ ! -f ".env" ]; then
    echo -e " ${BLUE}ℹ${NC} First run detected! Creating .env from template..."
    cp .env.example .env 2>/dev/null || true
    echo -e " ${GREEN}✓${NC} Created .env - Edit this file to add your API keys."
fi

if [ ! -f "user_settings.json" ]; then
    echo -e " ${BLUE}ℹ${NC} Creating user_settings.json from template..."
    cp user_settings.example.json user_settings.json 2>/dev/null || true
    echo -e " ${GREEN}✓${NC} Created user_settings.json"
fi

mkdir -p data 2>/dev/null || true

# -- 6. Install python requirements ---------------------------------
if [ ! -f ".venv/.ready" ]; then
    echo -e " ${BLUE}ℹ${NC} Installing required libraries [first time only]..."
    echo -e " ${DIM}   This may take 1-3 minutes depending on internet speed...${NC}"
    echo
    pip install --upgrade pip setuptools wheel -q
    pip install -r requirements.txt -q
    if [ $? -ne 0 ]; then
        echo
        echo -e " ${RED}✘${NC} ${BOLD}[ERROR] Some dependencies failed to install.${NC}"
        echo -e "   Please check your build tools and try running: pip install -r requirements.txt"
        exit 1
    fi
    echo "Done" > .venv/.ready
    echo -e " ${GREEN}✓${NC} Dependencies installed successfully."
else
    echo -e " ${GREEN}✓${NC} Dependencies ready."
fi

# -- 7. Launch Aiko -------------------------------------------------
echo
echo -e "${MAGENTA}============================================${NC}"
echo -e " ${BOLD}Neural Link Stable. Launching Aiko...${NC}"
echo -e "${MAGENTA}============================================${NC}"
echo

# Run the core launcher python script
python3 start_aiko_tauri.py

if [ $? -ne 0 ]; then
    echo
    echo -e "${MAGENTA}============================================${NC}"
    echo -e " ${RED}✘${NC} ${BOLD}Aiko exited with an error.${NC}"
    echo -e "   Check .logs/neural_hub.log for details."
    echo -e "${MAGENTA}============================================${NC}"
    echo
fi
