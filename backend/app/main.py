import logging
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from backend.app.core.config import settings
from backend.app.core.database import Base, engine
from backend.app.api import auth, core_routes, analytical_routes
from backend.app.agents.coordinator import initialize_agent_coordinator

# Setup logger configuration
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("Main")

# 1. Initialize DB tables (SQLAlchemy SQLite fallback)
logger.info("Initializing database schemas...")
Base.metadata.create_all(bind=engine)

# 2. Register cognitive agents to the event broker
logger.info("Initializing Agent Coordinator event subscribers...")
initialize_agent_coordinator()

app = FastAPI(
    title=settings.PROJECT_NAME,
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc"
)

# Set up CORS for frontend local development (React running on port 5173 / vite default)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # open for local development simplicity
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 3. Mount API routers
app.include_router(auth.router, prefix=settings.API_V1_STR)
app.include_router(core_routes.router, prefix=settings.API_V1_STR)
app.include_router(analytical_routes.router, prefix=settings.API_V1_STR)

@app.get("/")
def read_root():
    return {
        "status": "online",
        "service": settings.PROJECT_NAME,
        "api_docs": "/docs"
    }
