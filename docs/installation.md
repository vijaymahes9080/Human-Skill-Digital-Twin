# Human Skill Digital Twin - Installation Manual (Windows)

This document guides you through deploying the Human Skill Digital Twin platform locally.

## Prerequisite Dependencies

Before launching the installer, ensure your system has:
1. **Python 3.10 or higher**: [Download here](https://www.python.org/downloads/). Ensure you check the option **"Add python.exe to PATH"** during installation.
2. **Node.js (LTS version 18+)**: [Download here](https://nodejs.org/). This contains npm, needed to run the frontend local development server.

---

## 1. Automated Quick Start

1. Open a Command Prompt (cmd) in the project root directory.
2. Run the setup installer script:
   ```cmd
   scripts\setup.bat
   ```
   This script creates a Python virtual environment, installs pip packages, and builds frontend dependencies.
3. Once completed, launch both servers using:
   ```cmd
   scripts\run.bat
   ```
   This will open two terminal consoles starting the API server on port 8000 and the React client on port 5173.

---

## 2. Manual Installation

If you prefer to configure settings step-by-step:

### 2.1 Backend Setup
1. Open terminal in the `backend/` directory:
   ```cmd
   cd backend
   ```
2. Create and activate environment:
   ```cmd
   python -m venv venv
   call venv\Scripts\activate
   ```
3. Install dependencies:
   ```cmd
   pip install -r requirements.txt
   ```
4. Run migrations and database seeder:
   ```cmd
   python -m app.seed
   ```
5. Start development server:
   ```cmd
   python run.py
   ```

### 2.2 Frontend Setup
1. Open a separate terminal in the `frontend/` directory:
   ```cmd
   cd frontend
   ```
2. Install npm packages:
   ```cmd
   npm install
   ```
3. Boot the local client:
   ```cmd
   npm run dev
   ```
4. Navigate to `http://localhost:5173` inside your browser. Log in using `demo@digitaltwin.ai` with password `password123` to immediately view pre-seeded dashboard structures.
