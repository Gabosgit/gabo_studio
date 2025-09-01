"""
    API to manage Users, User-Profiles, User_Contracts, User_Events, Uploads and Accommodations
"""
from fastapi import FastAPI, APIRouter


# middleware: to handle CORS policy (Cross-Origin Resource Sharing)
# Access-Control-Allow-Origin allows requests from a React app
from fastapi.middleware.cors import CORSMiddleware

from app.datamanager.exceptions_handler import register_exception_handlers

# --- Import your router(s) ---
from app.api.endpoints import users
from app.api.endpoints import profiles
from app.api.endpoints import contracts
from app.api.endpoints import events
from app.api.endpoints import accommodations
from app.api.endpoints import uploads

# --- Main FastAPI Application Instance ---
app = FastAPI(
    title="FastAPI Application",
    description="A robust API built with FastAPI and SQLAlchemy.",
    version="0.1.0",
    docs_url="/docs",
    redoc_url="/redoc",
)
register_exception_handlers(app) #register the handlers.
router = APIRouter()

# --- Include your API Routers ---
app.include_router(users.router)
app.include_router(profiles.router)
app.include_router(contracts.router)
app.include_router(events.router)
app.include_router(accommodations.router)
app.include_router(uploads.router)

# Define the allowed origins list for frontend requests
origins = [
    "http://localhost:5173",   # Explicitly allow localhost for frontend
    "http://127.0.0.1:5173",   # Explicitly allow 127.0.0.1 for frontend using docker
    # Add any other origins that the frontend might use, e.g., if having other test environments
]

# Allows requests from your frontend (adjust origins as needed)
app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,  # allowed origins list for frontend (React). ["*"] Allows all origins
    allow_credentials=True,
    allow_methods=["*"],  # Allow all HTTP methods (GET, POST, etc.)
    allow_headers=["*"],  # Allow all headers
)

# ROOT ROUTE
@app.get("/", tags=["Home"])
async def root():
    """ Welcome message """
    return {"message": "Welcome to Create connections Pro"}

