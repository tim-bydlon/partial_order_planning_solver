import os
from fastapi import FastAPI
from dotenv import load_dotenv

load_dotenv()

app = FastAPI(
    title="Partial Order Planning Solver",
    description="A FastAPI service for partial order planning",
    version="0.1.0"
)

@app.get("/")
async def root():
    return {
        "message": "Partial Order Planning Solver API",
        "version": "0.1.0",
        "status": "running"
    }

@app.get("/health")
async def health_check():
    return {
        "status": "healthy",
        "api_host": os.getenv("API_HOST", "0.0.0.0"),
        "api_port": os.getenv("API_PORT", "8000"),
        "debug": os.getenv("API_DEBUG", "false").lower() == "true"
    }

@app.get("/solve")
async def solve_planning_problem():
    return {
        "message": "Planning solver endpoint - coming soon!",
        "todo": "Implement partial order planning algorithm"
    }