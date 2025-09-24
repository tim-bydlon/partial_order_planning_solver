# Partial Order Planning Solver - Project Context

## Project Overview
FastAPI-based partial order planning solver with Poetry + Docker setup, modeled after the MAGE episodic planning repository structure.

## Development Workflow

### Primary Development (Poetry - Fast Iteration)
**When to use:** Active feature development, debugging, rapid prototyping
**Pros:** Instant code changes, fast startup (~1-2 seconds), direct debugging, IDE integration
**Cons:** May miss container-specific issues, dependencies differ from production

```bash
poetry install                    # Install/update dependencies
poetry run poe serve             # Start with hot reload (uvicorn --reload)
# Server restarts automatically on code changes
# Direct access to Python debugger, print statements
# Uses local Python environment
```

**Development cycle:**
1. Edit code in `pop_solver/`
2. Save file → server auto-reloads
3. Test endpoint immediately
4. Repeat rapidly

### Production Testing (Docker - Before Commits)
**When to use:** Final validation, dependency verification, pre-deployment testing
**Pros:** Exact production environment, validates Docker build, catches container issues
**Cons:** Slower iteration (~10-30 seconds rebuild), requires Docker restart for code changes

```bash
docker-compose up --build        # Full rebuild + start
docker-compose up               # Use existing image (faster)
# Identical to production deployment
# Tests multi-stage build process
# Validates all dependencies in container
```

**Testing cycle:**
1. Complete feature development with Poetry
2. Build and test with Docker
3. Fix any container-specific issues
4. Commit when both workflows pass

### Key Commands
```bash
# Poetry tasks (defined in pyproject.toml)
poetry run poe serve    # uvicorn with --reload
poetry run poe test     # pytest tests/
poetry run poe format   # black + isort
poetry run poe lint     # flake8 + black --check + isort --check-only

# Docker commands
docker-compose up       # Start with existing image
docker-compose up --build  # Rebuild and start
docker build -t pop-solver .  # Build image only

# API testing
curl http://localhost:8000/        # API status
curl http://localhost:8000/health  # Environment config
curl http://localhost:8000/solve   # Planning endpoint (placeholder)
```

## Architecture Decisions

### Tech Stack
- **Python 3.12** (3.13 not available in Docker images yet)
- **Poetry** for dependency management
- **FastAPI + Uvicorn[standard]** for web API
- **Docker multi-stage** (python:3.12-bookworm base, not buster)
- **Docker Compose** (no version field - obsolete in newer versions)

### Project Structure
```
├── pop_solver/           # Main package
│   ├── __init__.py      # Version info
│   └── app.py           # FastAPI app with basic endpoints
├── pyproject.toml       # Poetry config + poe tasks
├── Dockerfile           # Multi-stage: builder + runtime
├── docker-compose.yaml  # Local orchestration
├── .env.example         # Environment template (committed)
├── .env                 # Local secrets (gitignored)
├── .dockerignore        # Build optimization
└── .gitignore           # Includes .env, .claude/, .idea/, venv_pop/
```

## Environment Configuration

### Development
- Copy `.env.example` to `.env`
- Docker Compose auto-loads `.env`
- Use `API_DEBUG=true` for development

### Production (Coolify)
- Set variables in Coolify dashboard UI
- No rebuild needed for config changes
- Use `API_DEBUG=false` for production

## Important Notes

### File Management
- `.env` is gitignored (secrets), `.env.example` is committed (template)
- `README_DEV.md` is gitignored if created (temporary notes)
- This `.claude/CLAUDE.md` is committed (persistent context)

### Docker Considerations
- Port 8000 may conflict - kill with `lsof -ti:8000 | xargs kill -9`
- Multi-stage build: poetry install in builder, copy venv to slim runtime
- Uses bookworm (not buster) due to Debian version support

### Docker Code Refresh Behavior (CRITICAL)

**Problem:** Code changes don't appear in running Docker container

**When rebuild is REQUIRED:**
- ✅ **Code changes in `pop_solver/`** - Python files are copied during build
- ✅ **pyproject.toml changes** - Dependencies copied during build
- ✅ **Dockerfile changes** - Build process modified
- ✅ **New Python files added** - Not in existing image

**When rebuild is NOT required:**
- ❌ **Environment variable changes** - Use `.env` file (runtime injection)
- ❌ **docker-compose.yaml changes** - Orchestration only (except build context)

**Proper workflow after code changes:**

```bash
# WRONG - Will show old code!
docker-compose up                    # Uses cached image with old code

# CORRECT - Forces rebuild with new code
docker-compose up --build            # Rebuilds image with latest code
# OR
docker-compose build && docker-compose up  # Explicit build then run
```

**Why this happens:**
1. `COPY pop_solver ./pop_solver` runs during **build time**
2. Code is **frozen** into the image layer
3. `docker-compose up` (without `--build`) uses **cached image**
4. Your code changes exist on host but **not in the image**

**Debugging stale code:**
```bash
# Check if image was rebuilt
docker images | grep pop-solver      # Look at creation time

# Force complete rebuild (nuclear option)
docker-compose build --no-cache     # Ignores all cached layers
docker-compose up

# Verify code in container
docker-compose exec app ls -la pop_solver/
docker-compose exec app cat pop_solver/app.py  # Check actual file content
```

**Performance tips:**
- Use `--build` only when code/dependencies change
- Use plain `up` only for environment variable changes
- Consider volume mounts for ultra-fast development (not production)

### Development Flow
1. **Develop with Poetry** (fast iteration)
2. **Test with Docker** (production validation)
3. **Commit when both work** (ensures deployment compatibility)

## Natural Language Planning Implementation Plan

### Phase 1: Copy Planning Module (Foundation)
**Status**: 🚀 Ready to Start
**Goal**: Import planning logic from episodic-planning repository into our codebase

**Tasks**:
1. **Copy planning directory structure** from episodic-planning into `pop_solver/planning/`
   - Include: `planner/`, `state/`, `operator/`, `plan/` subdirectories
   - Copy `planning_solving_functions.py` as the main interface
   - Update import paths to work within our repo structure
   - Add planning data files (JSON operators) to appropriate location

### Phase 2: MCP Server Integration (Tool Access)
**Status**: ⏸️ Waiting for Phase 1
**Goal**: Expose planning functions through local MCP server

**Tasks**:
2. **Create local STDIO MCP server** (`pop_solver/mcp_server.py`)
   - Expose planning functions as MCP tools: `apply_operator`, `create_plan`
   - Use `@mcp.tool()` decorators on wrapper functions
   - Handle robot/blockworld problem types appropriately
   - Run as STDIO subprocess within the same Docker container

### Phase 3: Agent Implementation (Intelligence Layer)
**Status**: ⏸️ Waiting for Phase 2
**Goal**: Build intelligent agent to handle natural language queries

**Tasks**:
3. **Implement planning agent** in `/solve` endpoint
   - **Simple classifier**: Use LLM prompt to determine problem type (robot vs blockworld)
   - **MCP client**: Connect to local STDIO server to access planning tools
   - **Basic agent loop**: Parse natural language → classify problem → call appropriate planning functions → format response

### Phase 4: Dependencies & Integration
**Status**: ⏸️ Waiting for Phase 3
**Goal**: Complete integration and dependency management

**Tasks**:
4. **Update project configuration**
   - Add MCP Python SDK to `pyproject.toml`
   - Add LLM client library (OpenAI/Anthropic) for classification and agent
   - Update Docker configuration if needed
   - Add environment variables for API keys

### Architecture Benefits
- **Simple start**: Direct function calls through MCP, no complex frameworks initially
- **Modular**: Planning logic isolated in MCP server, easy to test independently
- **Extensible**: Can add LangGraph or other agentic frameworks later
- **Container-friendly**: All components run locally, no external service dependencies

### Implementation Progress
- **Current Phase**: Phase 3 (Agent Implementation)
- **Phase 1**: ✅ **COMPLETED** - Planning module successfully integrated
  - ✅ Copied planning directory structure from episodic-planning repo
  - ✅ Fixed all import paths (7 files updated)
  - ✅ Replaced configuration references with local path resolution
  - ✅ Removed all external references and branding
  - ✅ **Comprehensive test suite**: 22 tests covering all functions and edge cases
  - ✅ **Tested successfully**: `apply_operator`, `create_plan`, and planner instantiation work
- **Phase 2**: ✅ **COMPLETED** - MCP Server Integration successfully implemented
  - ✅ Added MCP Python SDK dependency (`mcp[cli]` and `pytest-asyncio`)
  - ✅ Created `pop_solver/mcp_server.py` with FastMCP STDIO server
  - ✅ Implemented `apply_operator_tool` and `create_plan_tool` with @mcp.tool() decorators
  - ✅ **Comprehensive error handling**: LookupError exceptions → error strings, ValueError pass-through
  - ✅ **15 passing tests**: Verified MCP tools return identical outputs to direct functions
  - ✅ **Tool registration and schema validation**: Both tools properly registered with correct schemas
- **Next Steps**: Implement planning agent in `/solve` endpoint with LLM client integration
- **Plan Modifications**: _To be documented as we discover issues_


## Phase 3 Implementation Notes (CRITICAL for Next Claude)

### Agent Implementation Goal
Implement intelligent agent in `/solve` endpoint to handle natural language queries and connect them to planning functions via MCP server.

### MCP Server Integration (Ready to Use)
**MCP Server**: `pop_solver/mcp_server.py` - STDIO server with planning tools exposed
**Available MCP Tools:**
- `apply_operator_tool`: Apply operators to states
- `create_plan_tool`: Generate plans from start to goal conditions

**Usage Pattern:**
```python
# Start MCP server as subprocess
# Connect MCP client via STDIO transport
# Call tools: client.call_tool("apply_operator_tool", {...})
```

### Phase 3 Implementation Requirements

**1. Add LLM Client Dependency**
- Add OpenAI or Anthropic client to `pyproject.toml`
- Add API key environment variables to `.env.example`

**2. Create Agent in `/solve` Endpoint**
**File**: `pop_solver/app.py` (extend existing FastAPI app)
**Functionality**:
- **Natural Language Processing**: Parse user queries like "I need the robot to paint the ceiling"
- **Problem Classification**: Determine if query is robot or blockworld problem (only robot works currently)
- **State/Goal Extraction**: Extract start conditions and goal conditions from natural language
- **MCP Client Integration**: Connect to local MCP server via subprocess + STDIO
- **Planning Execution**: Call appropriate MCP tools based on query type
- **Response Formatting**: Return human-readable results

**3. MCP Client Implementation**
```python
# Example structure for MCP client integration
import subprocess
from mcp import client

# Start MCP server as subprocess
server_process = subprocess.Popen([
    "python", "pop_solver/mcp_server.py"
], stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE)

# Connect MCP client via STDIO
client = mcp.Client(transport='stdio', process=server_process)

# Call planning tools
result = await client.call_tool("create_plan_tool", {
    "start_conditions": ["On(Robot, Floor)", "Dry(Ladder)", "Dry(Ceiling)"],
    "goal_conditions": ["Painted(Ceiling)"],
    "problem_type": "robot"
})
```

### Critical Technical Details (From Phase 1 & 2)

**Available Operators**: `['climb-ladder', 'descend-ladder', 'paint-ceiling', 'paint-ladder']`

**State Conditions Format**: `['On(Robot, Floor)', 'Dry(Ladder)', 'Dry(Ceiling)']`

**Goal Conditions**: `['Painted(Ceiling)', 'Painted(Ladder)']`

**Known Issues:**
- apply_operator returns start state instead of result state (but validation works)
- Only 'robot' problem type works, 'blockworld' returns graceful error
- LookupError exceptions handled properly by MCP tools

### Agent Architecture

**Simple Classification Approach:**
1. Use LLM prompt to analyze natural language query
2. Extract key elements: problem type, current state, desired goals
3. Convert to planning function format
4. Call MCP tools via local client
5. Format and return results

**Example User Queries to Handle:**
- "Help the robot paint the ceiling"
- "The robot is on the floor, ladder and ceiling are dry, I want the ceiling painted"
- "Create a plan to paint both the ceiling and ladder"

### Success Criteria for Phase 3
- `/solve` endpoint accepts natural language queries
- Agent correctly classifies and extracts planning elements
- MCP client successfully communicates with local server
- Returns human-readable planning results
- Error handling for invalid queries and planning failures

### Test Strategy for Phase 3
- **Agent endpoint tests**: Test `/solve` endpoint with various natural language queries
- **MCP client-server integration**: Verify full communication pipeline works
- **Error handling**: Test invalid queries, planning failures, and MCP communication errors
- **Natural language processing**: Validate extraction of planning elements from user queries

## Documentation References

### MCP (Model Context Protocol)
- [MCP Introduction](https://modelcontextprotocol.io/docs/getting-started/intro) - Core concepts and architecture overview
- [MCP Architecture](https://modelcontextprotocol.io/docs/concepts/architecture) - Client-server protocol, tools, resources, and transports
- [MCP Server Development](https://modelcontextprotocol.io/docs/develop/build-server) - Building STDIO servers with @mcp.tool() decorators
- [MCP Client Development](https://modelcontextprotocol.io/docs/develop/build-client) - Python client implementation for connecting to STDIO servers

### Planning Theory
- _To be added as we research planning algorithms and PDDL specifications_

## Implementation Status
- ✅ Poetry + Docker foundation complete
- ✅ FastAPI app with health/status endpoints
- ✅ Environment variable system working
- ✅ Build and deployment ready
- ✅ **Phase 1**: Copy Planning Module (COMPLETED)
- ✅ **Phase 2**: MCP Server Integration (COMPLETED)
- 🚀 **Phase 3**: Agent Implementation (Ready to Start)
- ⏸️ **Phase 4**: Dependencies & Integration (Waiting)