import os
import json
import time
from fastapi import FastAPI, HTTPException, Request, Response
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded

from backend.agent import run_disaster_analysis
from backend.report_generator import generate_pdf
from backend.ml_layer.predict import predictor
from backend.ai_brain import brain
from backend.logger import log_request

limiter = Limiter(key_func=get_remote_address)
app = FastAPI(title="DisasterMind API")

app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

class AnalysisRequest(BaseModel):
    region_name: str
    lat: float
    lon: float
    bbox: list[float]  # [lat_min, lon_min, lat_max, lon_max]

@app.middleware("http")
async def add_process_time_header_and_log(request: Request, call_next):
    start_time = time.time()
    response = await call_next(request)
    duration_ms = int((time.time() - start_time) * 1000)
    # Exclude /health from aggressive logging if needed, but logging all for now
    log_request(
        event="HTTP Request",
        region="System",
        user_ip=request.client.host if request.client else "unknown",
        method=request.method,
        url=str(request.url),
        status_code=response.status_code,
        duration_ms=duration_ms
    )
    return response

@app.get("/health")
def health_check():
    return {
        "status": "online",
        "models": {
            "flood_model": "loaded" if predictor.flood_session else "missing",
            "severity_model": "loaded" if predictor.severity_session else "missing"
        },
        "groq_llm": "connected" if brain.client else "missing_api_key"
    }

@app.get("/regions")
def get_regions():
    return {
        "regions": [
            {
                "id": "wayanad",
                "name": "Wayanad, Kerala",
                "lat": 11.6854,
                "lon": 76.1320,
                "bbox": [11.5, 75.9, 11.9, 76.3],
                "context": "High risk of landslides due to steep terrain and heavy monsoon rains."
            },
            {
                "id": "kamrup",
                "name": "Kamrup, Assam",
                "lat": 26.3161,
                "lon": 91.5984,
                "bbox": [26.1, 91.3, 26.5, 91.8],
                "context": "Severe riverine flooding risk from Brahmaputra basin."
            },
            {
                "id": "chamoli",
                "name": "Chamoli, Uttarakhand",
                "lat": 30.2736,
                "lon": 79.3234,
                "bbox": [30.0, 79.1, 30.5, 79.5],
                "context": "Vulnerable to glacial bursts, flash floods, and seismic activity."
            }
        ]
    }

@app.post("/analyze")
@limiter.limit("10/minute")
async def analyze_region(request: Request, req: AnalysisRequest):
    try:
        # Expected tuple for bbox: (lat_min, lon_min, lat_max, lon_max)
        payload = run_disaster_analysis(req.region_name, req.lat, req.lon, tuple(req.bbox))
        return payload
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/demo/{region}")
def get_demo_analysis(region: str):
    cache_file = os.path.join(os.path.dirname(__file__), "demo_cache", f"{region}.json")
    if os.path.exists(cache_file):
        with open(cache_file, "r") as f:
            return json.load(f)
    raise HTTPException(status_code=404, detail="Demo cache not found for this region.")

@app.post("/report/pdf")
async def get_pdf_report(payload: dict):
    try:
        pdf_bytes = generate_pdf(payload)
        return StreamingResponse(
            pdf_bytes,
            media_type="application/pdf",
            headers={
                "Content-Disposition": f"attachment; filename=DisasterMind_Report.pdf"
            }
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
