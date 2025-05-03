# AI Travel Planner

An intelligent travel planning system using LangChain and specialized agents to generate personalized travel itineraries, event recommendations, and restaurant suggestions.

## Features

- Generate detailed travel itineraries based on preferences
- Find local events and activities
- Get restaurant recommendations
- All recommendations are tailored to your location and preferences

## Setup

1. Clone the repository:
```bash
git clone https://github.com/yourusername/trip_planner.git
cd trip_planner
```

2. Create a virtual environment and activate it:
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

3. Install dependencies:
```bash
pip install -r requirements.txt
```

4. Create a `.env` file in the project root with your OpenAI API key:
```
OPENAI_API_KEY=your_api_key_here
```

5. Start the server:
```bash
uvicorn main:app --reload --port 9000
```

## API Usage

### Generate an Itinerary

```bash
curl -X POST http://localhost:9000/api/itinerary \
  -H "Content-Type: application/json" \
  -d '{
    "destination": "Seattle",
    "start_date": "2024-04-01",
    "days": 2,
    "preferences": ["culture", "food", "nature"],
    "budget": 500
  }'
```

### Find Events

```bash
curl -X POST http://localhost:9000/api/events \
  -H "Content-Type: application/json" \
  -d '{
    "location": "Seattle",
    "event_date": "2024-04-01",
    "preferences": ["music", "sports", "culture"],
    "budget": 100
  }'
```

### Get Restaurant Recommendations

```bash
curl -X POST http://localhost:9000/api/restaurants \
  -H "Content-Type: application/json" \
  -d '{
    "location": "Seattle",
    "restaurant_date": "2024-04-01",
    "cuisine_preferences": ["italian", "japanese", "american"],
    "price_range": "$$",
    "party_size": 2
  }'
```

## API Documentation

Once the server is running, visit http://localhost:9000/docs for the interactive API documentation.

## Development

### Running Tests

```bash
pytest
```

### Code Formatting

```bash
black .
isort .
```

### Type Checking

```bash
mypy .
```

## Project Structure

```
trip_planner/
├── agents/                 # Specialized agents for different tasks
│   ├── itinerary_agent.py
│   ├── events_agent.py
│   └── restaurant_agent.py
├── core/                   # Core functionality
│   ├── base_agent.py
│   └── config.py
├── models/                 # Data models and schemas
│   └── schemas.py
├── main.py                 # FastAPI application entry point
├── requirements.txt        # Project dependencies
└── README.md              # This file
```

## Contributing

1. Fork the repository
2. Create a feature branch
3. Commit your changes
4. Push to the branch
5. Create a Pull Request

## License

This project is licensed under the MIT License - see the LICENSE file for details. 