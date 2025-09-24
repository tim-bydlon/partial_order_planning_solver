import os
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from dotenv import load_dotenv
from typing import Optional

load_dotenv()

app = FastAPI(
    title="Partial Order Planning Solver",
    description="A FastAPI service for partial order planning with natural language interface",
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

class PlanningQuery(BaseModel):
    """Request model for planning queries"""
    query: str
    api_key: Optional[str] = None  # Optional API key override


class PlanningResponse(BaseModel):
    """Response model for planning queries"""
    query: str
    success: bool
    result: str
    details: Optional[dict] = None


@app.post("/solve", response_model=PlanningResponse)
async def solve_planning_problem(request: PlanningQuery):
    """
    Process natural language planning queries.

    Examples:
    - "Help the robot paint the ceiling"
    - "The robot needs to paint both the ceiling and the ladder"
    - "What happens if the robot climbs the ladder?"
    """
    try:
        # Import here to avoid circular dependencies and only load when needed
        from pop_solver.agent import PlanningAgent

        # Initialize agent with optional API key override
        agent = PlanningAgent(api_key=request.api_key)

        # Process the query
        result = await agent.process_query(request.query)

        # Return formatted response
        return PlanningResponse(
            query=request.query,
            success=result["success"],
            result=result["formatted_result"],
            details={
                "parsed": result["parsed"],
                "raw_result": result["raw_result"]
            }
        )
    except ValueError as e:
        # Missing API key or configuration error
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        # Unexpected error
        raise HTTPException(status_code=500, detail=f"Failed to process query: {str(e)}")