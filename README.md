# Partial Order Planning Solver

A FastAPI-based partial order planning solver with natural language interface.

## Development

```bash
# Install dependencies
poetry install

# Run the server
poetry run poe serve

# Run tests
poetry run poe test

# Format code
poetry run poe format

# Lint code
poetry run poe lint
```

## API Endpoints

- `GET /` - API status
- `GET /health` - Health check with environment info
- `POST /solve` - Planning solver endpoint (coming soon)