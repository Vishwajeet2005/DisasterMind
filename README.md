# DisasterMind 🌪️
*Autonomous Disaster Response Intelligence Agent for India.*

> **The Wayanad Hook** 
> When landslides ravage steep terrains or rivers breach their banks, every second counts. DisasterMind was built to prevent catastrophic intelligence failures during events like the devastating Wayanad landslides. By fusing real-time satellite telemetry, machine learning predictive models, and LLM tactical reasoning, DisasterMind autonomously synthesizes critical situation reports before human responders even reach the ground.

## Architecture Summary
DisasterMind operates as a continuous, autonomous pipeline:
1. **Data Ingestion**: Hooks into global live telemetry APIs (NASA, Earth Engine, Open-Meteo) bounding specific coordinate regions.
2. **Machine Learning Pipeline**: Streams raw sensor data through an ONNX ensemble (`XGBoost` for Flood Risk, `Random Forest` for Severity Classification) to establish mathematical consensus.
3. **AIBrain (LLM Reasoning Layer)**: Consumes the raw data and ML consensus to synthetically generate highly structured, tactical situation reports using `llama-3.3-70b-versatile`.
4. **Tactical UI**: Renders the intelligence through a strict, zero-gradient Palantir Gotham aesthetic interface built on React & Leaflet.

## Tech Stack
- **Frontend**: React.js, Vite, Leaflet, CartoDB Maps, Lucide React
- **Backend**: FastAPI, Uvicorn, SlowAPI, ReportLab
- **Machine Learning**: XGBoost, Scikit-Learn, ONNX Runtime
- **LLM Reasoning**: Groq SDK (`llama-3.3-70b-versatile`)
- **Containerization**: Docker, Docker Compose

## Real-Time Data Sources
- **NASA FIRMS (VIIRS)**: Live thermal anomalies and hotspot tracking.
- **Open-Meteo**: High-precision 3-day precipitation and wind forecasting.
- **OpenTopoData (SRTM90m)**: Digital Elevation Models (DEM) for flood and landslide vulnerabilities.
- **Overpass API (OSM)**: OpenStreetMap querying for road network integrity.
- **Google Earth Engine (COPERNICUS/S2_SR_HARMONIZED)**: Optical satellite imaging.

## Getting Started

### Prerequisites
- Docker and Docker Compose installed.
- (Optional) Groq API Key set in `.env.example` as `GROQ_API_KEY`.

### Startup Commands
To launch the entire DisasterMind stack:

```bash
# 1. Clone the repository
git clone https://github.com/Vishwajeet2005/DisasterMind.git
cd disastermind

# 2. Build and launch containers
docker-compose up --build
```

- **Frontend**: Accessible at `http://localhost:3000`
- **Backend API**: Accessible at `http://localhost:8000`
- **API Documentation**: Accessible at `http://localhost:8000/docs`
