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
- **Current Phase**: Phase 3 ✅ **COMPLETED**
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
- **Phase 3**: ✅ **COMPLETED** - Natural Language Agent successfully implemented
  - ✅ Added Anthropic SDK dependency (v0.40.0) using Claude 3.5 Sonnet model
  - ✅ Created `pop_solver/mcp_client.py` - STDIO client for MCP server communication
  - ✅ Created `pop_solver/agent.py` - Natural language processing with Sonnet
  - ✅ Updated `/solve` endpoint to POST with natural language query support
  - ✅ **10 passing tests**: MCP client, agent parsing, and endpoint integration
  - ✅ **Docker validated**: Successfully builds and runs with all dependencies
- **Next Steps**: Ready for Phase 4 - Extended capabilities and optimizations
- **Plan Modifications**: _None - implementation completed as designed_


## Phase 3 COMPLETED - Natural Language Interface ✅

### What Was Built
- **MCP Client** (`pop_solver/mcp_client.py`) - STDIO-based communication with MCP server
- **Planning Agent** (`pop_solver/agent.py`) - Claude Sonnet 4 integration for NLP
- **API Endpoint** (`/solve`) - POST endpoint accepting natural language queries
- **Comprehensive Tests** - 47 total tests passing (22 planning + 15 MCP + 10 Phase 3)

### Critical Working Details
- **Model**: Using `claude-sonnet-4-20250514` (NOT claude-3-5-sonnet variants)
- **Environment**: API key loaded from `.env` file via `python-dotenv`
- **Docker**: Fully working with `env_file: - .env` in docker-compose.yaml
- **Testing**: Mocked tests work without API key, real tests require `ANTHROPIC_API_KEY`

## Phase 4: Blocks World Implementation (NEXT TASK)

### Goal
Implement the classic blocks world planning domain as a second domain alongside the robot painting problem.

### What is Blocks World?
A classic AI planning domain consisting of wooden blocks on a table. The goal is to rearrange blocks into specific configurations through a series of moves. Only one block can be moved at a time, and blocks underneath others cannot be moved.

### Current Blockworld Status
- **Classes exist but not implemented**:
  - `pop_solver/planning/planner/instances/blockworld_planner.py` (empty stub)
  - `pop_solver/planning/state/instances/blockworld_state.py` (likely needs creation)
- **Error handling in place**: Returns "Blockworld planner not implemented" gracefully
- **Tests ready**: Blockworld tests exist but are skipped/mocked

### Implementation Requirements

#### 1. Blocks World Domain Definition
**Classic blocks world problem:**
- **Objects**: Blocks (A, B, C, etc.) and a table
- **States**:
  - `On(A, B)` - Block A is on block B
  - `On(A, Table)` - Block A is on the table
  - `Clear(A)` - Nothing is on top of block A (can be moved)
  - `Clear(Table)` - Table always has space (always true)

#### 2. Blocks World Operators
**Operators using precondition/postcondition format:**
```json
{
  "name": "pickup",
  "preconditions": ["Clear(block)", "On(block, Table)"],
  "postconditions": ["Holding(block)", "¬On(block, Table)", "¬Clear(block)"]
}

{
  "name": "putdown",
  "preconditions": ["Holding(block)"],
  "postconditions": ["On(block, Table)", "Clear(block)", "¬Holding(block)"]
}

{
  "name": "stack",
  "preconditions": ["Holding(block1)", "Clear(block2)"],
  "postconditions": ["On(block1, block2)", "Clear(block1)", "¬Holding(block1)", "¬Clear(block2)"]
}

{
  "name": "unstack",
  "preconditions": ["On(block1, block2)", "Clear(block1)"],
  "postconditions": ["Holding(block1)", "Clear(block2)", "¬On(block1, block2)", "¬Clear(block1)"]
}
```
**Note**: Postconditions include BOTH positive effects (what becomes true) and negative effects (what becomes false, marked with ¬)

#### 3. Files to Modify/Create

**Create/Implement:**
1. `pop_solver/planning/planner/instances/blockworld_planner.py`
2. `pop_solver/planning/state/instances/blockworld_state.py`
3. `pop_solver/planning/operator/instances/blockworld_operators.json`

**Update:**
1. `planning_solving_functions.py` - Remove the ValueError for blockworld
2. `pop_solver/agent.py` - Add blockworld examples to prompts
3. Tests - Enable blockworld tests

#### 4. Natural Language Examples for Blocks World
```
"Stack block A on block B"
"Move all blocks to the table"
"Build a tower with A on B on C"
"Clear block C so it can be moved"
"Rearrange blocks from [A on B, C on table] to [B on C, A on table]"
```

### Critical Implementation Notes

**1. Planning Algorithm**: This system uses **Partial Order Planning (POP)**
   - Builds separate partial plans for each goal condition
   - Reorders plans to avoid conflicts
   - Connects partial plans together
   - Uses backward chaining from goals to start state

**2. Operator Format**: Uses **precondition/postcondition** format (NOT STRIPS add/delete effects)
   - **Preconditions**: List of conditions that must be true before operator applies
   - **Postconditions**: ALL state changes including:
     - Positive effects: what becomes true (e.g., `"Painted(Ceiling)"`)
     - Negative effects: what becomes false (e.g., `"¬Dry(Ceiling)"`)
   - Both positive and negative effects are in a single postconditions list

**3. Implementation Details**:
   - States are managed as sets of conditions
   - Operators defined in JSON files (e.g., `robot_painting_operators.json`)
   - State classes handle applying operators and checking conditions
   - Plan class builds plans using **reverse search** from goal to start (line 19-27 in `plan.py`)
   - Plans are reversed after construction (line 30 in `plan.py`)
   - `precondition_for_reverse_search` is key for backward chaining (line 23 in `plan.py`)

**4. Blocks World Considerations**:
   - Use same precondition/postcondition format as robot domain
   - State predicates: `On(A, B)`, `Clear(A)`, `Holding(A)`
   - Operators will need dynamic handling for parameterized blocks (A, B, C, etc.)

**5. Testing**: Enable the skipped blockworld tests once implementation is complete

## CRITICAL NOTES FOR NEXT CLAUDE ITERATION

### Working System Architecture
1. **MCP Server** (`mcp_server.py`) exposes planning functions as tools via STDIO
2. **MCP Client** (`mcp_client.py`) connects to server as subprocess, handles JSONRPC communication
3. **Agent** (`agent.py`) uses Claude Sonnet 4 to parse natural language and call MCP tools
4. **API** (`app.py`) provides `/solve` endpoint for natural language queries

### Key Technical Details
- **Model**: `claude-sonnet-4-20250514` (NOT 3.5 variants - they don't work)
- **Python**: 3.12+ required (3.13 works but shows warnings)
- **Virtual Env**: Using Poetry (removed old `venv_pop/`)
- **Docker**: Loads `.env` automatically via `env_file` directive
- **Tests**: 47 passing (10 Phase 3 use mocks, 2 require API key for real tests)

### Known Issues & Solutions
1. **apply_operator bug**: Returns start state instead of result state (precondition validation works though)
   - Bug is in lines 179-186 of `robot_painting_state.py` - hardcoded state changes
2. **JSON parsing in Docker**: Curl requests may have quote escaping issues - test with Python client
3. **Poetry + PyCharm**: Use Poetry plugin or manually set interpreter to Poetry venv path
4. **Operator has TODO**: Line 11 in `operator.py` - Blockworld needs dynamic operators

### Phase 4 Blockworld TODO
1. Create `blockworld_planner.py` implementation
2. Create `blockworld_operators.json` with pickup/putdown/stack/unstack
3. Remove ValueError in `planning_solving_functions.py`
4. Update agent prompts to handle blocks world queries
5. Add blocks world examples to tests

### Important File Locations
- **Planning Logic**: `pop_solver/planning/planning_solving_functions.py`
- **MCP Tools**: `pop_solver/mcp_server.py`
- **NLP Agent**: `pop_solver/agent.py`
- **API Endpoint**: `pop_solver/app.py`
- **Tests**: `tests/test_phase3_integration.py`

## Documentation References

### MCP (Model Context Protocol)
- [MCP Introduction](https://modelcontextprotocol.io/docs/getting-started/intro) - Core concepts and architecture overview
- [MCP Architecture](https://modelcontextprotocol.io/docs/concepts/architecture) - Client-server protocol, tools, resources, and transports
- [MCP Server Development](https://modelcontextprotocol.io/docs/develop/build-server) - Building STDIO servers with @mcp.tool() decorators
- [MCP Client Development](https://modelcontextprotocol.io/docs/develop/build-client) - Python client implementation for connecting to STDIO servers

### Planning Theory
- [Partial Order Planning](https://en.wikipedia.org/wiki/Partial-order_planning) - The planning algorithm used in this system
- [Blocks World](https://en.wikipedia.org/wiki/Blocks_world) - Classic AI planning domain overview
- **Key Clarification**: This system uses:
  - **POP Algorithm**: For planning (partial ordering, conflict resolution)
  - **Precondition/Postcondition Format**: For operators (NOT classic STRIPS add/delete effects)
  - Postconditions contain BOTH positive and negative effects in one list
- _PDDL specifications to be added as we expand domain support_

## Implementation Status
- ✅ Poetry + Docker foundation complete
- ✅ FastAPI app with health/status endpoints
- ✅ Environment variable system working
- ✅ Build and deployment ready
- ✅ **Phase 1**: Copy Planning Module (COMPLETED)
- ✅ **Phase 2**: MCP Server Integration (COMPLETED)
- ✅ **Phase 3**: Agent Implementation (COMPLETED)
- 🚀 **Phase 4**: Extended capabilities and optimizations (Ready when needed)