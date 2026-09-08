# 🌍 TripGenie: AI Multi-Agent Travel Planner

TripGenie is a full-stack, AI-powered travel planning platform. It leverages a stateful multi-agent architecture to autonomously gather real-time data, optimize budgets, and generate highly personalized travel itineraries. 

Users can specify their destination, travel dates, budget, and travel companions. The system asynchronously fetches flights, hotels, weather, and attractions, evaluates them using LLMs, and outputs a daily itinerary. Users can also export their itinerary as a beautifully formatted PDF and share it via an AWS S3 presigned URL.

## 🚀 Key Features

*   **Multi-Agent Orchestration**: Powered by LangGraph, the workflow utilizes specialized agent nodes (`planner`, `critic`, `router`) to recursively refine and validate the itinerary against the user's budget.
*   **Multi-LLM Architecture**: 
    *   **Groq**: Extremely fast parsing of raw JSON responses into strict Pydantic schemas.
    *   **Mistral AI**: Intelligent generation (Planner) and strict evaluation (Critic) of the final itinerary.
*   **Real-time Data Ingestion**: Concurrently fetches data using `asyncio` and `httpx` from external APIs (SerpAPI for Google Flights/Hotels, Open-Meteo for weather, Nominatim for attractions).
*   **PDF Export & Cloud Sharing**: Generates clean, formatted PDFs via `xhtml2pdf` and `markdown`, and uploads them to AWS S3, returning a secure 24-hour shareable link.
*   **Stateful Memory**: Utilizes SQLite checkpointing with LangGraph to maintain conversation/thread state across the user session.
*   **Microservices Architecture**: Decoupled FastAPI backend and Streamlit frontend.

## 🛠️ Tech Stack

*   **Frontend**: Streamlit
*   **Backend**: FastAPI, Uvicorn, Pydantic
*   **AI/Agents**: LangGraph, LangChain, Groq API, Mistral AI API
*   **Databases**: SQLite (via `aiosqlite`)
*   **Cloud & Export**: AWS S3 (`boto3`), `xhtml2pdf`, `markdown`
*   **Data Sources**: SerpAPI, Open-Meteo, OpenStreetMap (Nominatim)

## 📁 Project Structure

```
├── backend/
│   ├── agents/
│   │   ├── critic.py      # Mistral AI agent evaluating budget and feasibility
│   │   ├── parser.py      # Groq agent strictly parsing JSON into Pydantic models
│   │   ├── planner.py     # Mistral AI agent generating the daily itinerary
│   │   └── router.py      # Initial node to process user input
│   ├── graph/
│   │   ├── edges.py       # Conditional logic routing (e.g., looping back if critic fails)
│   │   └── workflow.py    # Main LangGraph compilation and parallel execution logic
│   ├── schemas/
│   │   ├── models.py      # Pydantic schemas for Flights, Hotels, Weather, Attractions
│   │   └── state.py       # TypedDict representing the graph's global state
│   ├── tools/
│   │   ├── attractions.py # Nominatim API integration
│   │   ├── cache_utils.py # Local caching decorators
│   │   ├── travel_inventory.py # SerpAPI (Flights & Hotels) integration
│   │   └── weather.py     # Open-Meteo API integration
│   ├── utils/
│   │   └── pdf_generator.py # Markdown to PDF conversion and S3 upload
│   ├── app.py             # FastAPI entry point and API routes
│   └── config.py          # Environment variable configurations
├── frontend/
│   └── app.py             # Streamlit UI
├── .env.example           # Example environment variables
├── requirements.txt       # Python dependencies
└── checkpoints.sqlite     # LangGraph local state storage (Git-ignored)
```

