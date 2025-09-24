# Partial Order Planning Solver

A natural language planning system that uses Claude AI to understand planning queries and solve them using partial order planning algorithms.

## Features

- 🤖 **Natural Language Interface**: Ask planning questions in plain English
- 📋 **Robot Painting Domain**: Solve planning problems for a robot that can climb ladders and paint
- 🔧 **MCP Server Integration**: Modular architecture using Model Context Protocol
- 🐳 **Docker Support**: Easy deployment with Docker Compose
- ⚡ **Fast Development**: Poetry-based development with hot reload

## Quick Start

### Prerequisites

- Docker and Docker Compose (for production)
- Python 3.12+ and Poetry (for development)
- Anthropic API key for Claude AI

### Installation

1. **Clone the repository:**
```bash
git clone <repository-url>
cd partial_order_planning_solver
```

2. **Set up environment variables:**
```bash
cp .env.example .env
```

3. **Edit `.env` and add your Anthropic API key:**
```
ANTHROPIC_API_KEY=sk-ant-your-actual-api-key-here
```

### Running with Docker (Recommended)

1. **Build and start the application:**
```bash
docker-compose up --build
```

2. **The API will be available at:** `http://localhost:8000`

3. **To run in detached mode:**
```bash
docker-compose up -d
```

4. **To stop the application:**
```bash
docker-compose down
```

### Running with Poetry (Development)

```bash
# Install dependencies
poetry install

# Run the server with hot reload
poetry run poe serve

# Run tests
poetry run poe test

# Format code
poetry run poe format

# Lint code
poetry run poe lint
```

## API Usage

### Health Check

```bash
curl http://localhost:8000/health
```

Response:
```json
{
  "status": "healthy",
  "api_host": "0.0.0.0",
  "api_port": "8000",
  "debug": false
}
```

### Solve Planning Problems

Send natural language queries to the `/solve` endpoint:

```bash
curl -X POST http://localhost:8000/solve \
  -H "Content-Type: application/json" \
  -d '{"query": "Help the robot paint the ceiling"}'
```

### Example Queries

Try these natural language queries:

1. **Create a plan:**
   - "Help the robot paint the ceiling"
   - "The robot needs to paint both the ceiling and the ladder"
   - "I want the ladder and ceiling to be painted"

2. **Apply single operators:**
   - "What happens if the robot climbs the ladder?"
   - "Show me what changes when the robot paints the ceiling"

3. **Complex scenarios:**
   - "The robot is on the ladder, now paint the ceiling"
   - "Robot is on the floor with a wet ladder, what can it do?"

## API Endpoints

- `GET /` - API status
- `GET /health` - Health check with environment info
- `POST /solve` - Natural language planning solver

### Request Format

**POST** `/solve`

```json
{
  "query": "Your natural language planning query",
  "api_key": "optional-api-key-override"
}
```

**Response Format:**

```json
{
  "query": "The original query",
  "success": true,
  "result": "Human-readable planning solution",
  "details": {
    "parsed": {
      "problem_type": "robot",
      "current_state": ["On(Robot, Floor)", ...],
      "goals": ["Painted(Ceiling)"],
      "query_type": "plan"
    },
    "raw_result": "Technical planning output"
  }
}
```

## Planning Domain

The system currently supports a **robot painting domain** with:

### States
- `On(Robot, Floor)` or `On(Robot, Ladder)` - Robot location
- `Dry(Ladder)` or `¬Dry(Ladder)` - Ladder condition
- `Dry(Ceiling)` or `¬Dry(Ceiling)` - Ceiling condition
- `Painted(Ladder)` - Ladder is painted
- `Painted(Ceiling)` - Ceiling is painted

### Operators
- `climb-ladder` - Robot climbs from floor to ladder
- `descend-ladder` - Robot descends from ladder to floor
- `paint-ceiling` - Paint the ceiling (requires robot on ladder)
- `paint-ladder` - Paint the ladder (requires robot on floor)

## Troubleshooting

### Docker Issues

1. **Port already in use:**
```bash
lsof -ti:8000 | xargs kill -9
```

2. **Rebuild after code changes:**
```bash
docker-compose up --build
```

### API Key Issues

- Ensure `ANTHROPIC_API_KEY` is set in `.env`
- The system uses Claude Sonnet 4 model
- Check your API key has proper permissions

## License

[Your License Here]