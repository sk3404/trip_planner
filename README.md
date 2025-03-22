# AI Travel Planner

An intelligent travel planning system that uses specialized AI agents to create personalized travel experiences.

## Features

- **Itinerary Agent**: Creates optimized travel itineraries based on preferences and constraints
- **Events Agent**: Recommends and books events and activities
- **Restaurant Agent**: Suggests restaurants and dining experiences

## Project Structure

```
trip_planner/
├── agents/
│   ├── itinerary_agent.py
│   ├── events_agent.py
│   └── restaurant_agent.py
├── core/
│   ├── __init__.py
│   ├── config.py
│   └── base_agent.py
├── models/
│   ├── __init__.py
│   └── schemas.py
├── utils/
│   ├── __init__.py
│   └── helpers.py
├── main.py
├── requirements.txt
└── README.md
```

## Setup

1. Create a virtual environment:
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

2. Install dependencies:
```bash
pip install -r requirements.txt
```

3. Set up environment variables:
```bash
cp .env.example .env
# Edit .env with your API keys and configuration
```

## Usage

Run the application:
```bash
python main.py
```

## Development

- Format code: `black .`
- Sort imports: `isort .`
- Type checking: `mypy .`
- Run tests: `pytest` 