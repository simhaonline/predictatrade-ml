# Predict-A-Trade vNext

A comprehensive trading platform with advanced analytics and AI-powered decision making.

## Project Structure

This project follows a monorepo layout with clear separation of concerns:

- `src/` - Backend Python services and CLI
- `frontend/` - Next.js 15 Application
- `tests/` - Test suite
- `config/` - Configuration files
- `docs/` - Documentation
- `scripts/` - Utility and automation scripts

## Getting Started

### Prerequisites

- Python 3.8+
- Node.js 18+
- Docker and Docker Compose (for full stack deployment)
- PostgreSQL
- Redis/Valkey

### Installation

1. Clone the repository
2. Install Python dependencies:
   ```bash
   pip install -e .
   pip install -e .[dev]
   ```
3. Install frontend dependencies:
   ```bash
   cd frontend
   npm install
   ```

### Running Tests

```bash
# Run all tests
pytest

# Run only unit tests
pytest tests/unit/

# Run only integration tests
pytest tests/integration/

# Run tests with coverage
pytest --cov=src --cov-report=html
```

### Development

For detailed development instructions, see the documentation in the `docs/` directory.

## License

Proprietary and confidential.