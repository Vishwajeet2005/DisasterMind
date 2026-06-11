"""
DisasterMind — FastAPI Application
Provides all HTTP endpoints, middleware (CORS, rate limiting, request logging),
and the PDF report download route.
"""

import json
import os
import time
from pathlib import Path
from typing import Optional

from fastapi import FastAPI, HTTPException, Request, Response
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, StreamingResponse
from pydantic import BaseModel
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded
from slowapi.util import get_remote_address
from dotenv import load_dotenv

from agent import run_disaster_analysis
from logger import log_request, log_error
from report_generator import generate_pdf
from ml_layer.predict import predictor

load_dotenv()

# ── Rate limiter ──────────────────────────────────────────────────────────────
limiter = Limiter(key_func=get_remote_address)

# ── App ───────────────────────────────────────────────────────────────────────
app = FastAPI(
    title       = "DisasterMind API",
    description = "Autonomous Disaster Response Intelligence Agent",
    version     = "1.0.0",
)
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

# ── CORS ──────────────────────────────────────────────────────────────────────
app.add_middleware(
    CORSMiddleware,
    allow_origins     = ["http://localhost:3000", "http://127.0.0.1:3000"],
    allow_credentials = True,
    allow_methods     = ["*"],
    allow_headers     = ["*"],
)

# ── Demo cache directory ──────────────────────────────────────────────────────
DEMO_CACHE_DIR = Path(__file__).parent / "demo_cache"
DEMO_CACHE_DIR.mkdir(exist_ok=True)

# ── Preset regions ────────────────────────────────────────────────────────────
PRESET_REGIONS = {
    "wayanad": {
        "id":      "wayanad",
        "name":    "Wayanad, Kerala",
        "lat":     11.6,
        "lon":     76.0,
        "bbox":    {"lat_min": 11.3, "lat_max": 11.9, "lon_min": 75.7, "lon_max": 76.4},
        "context": "Landslide July 2024 — 300+ deaths",
    },
    "assam": {
        "id":      "assam",
        "name":    "Kamrup, Assam",
        "lat":     26.2,
        "lon":     91.7,
        "bbox":    {"lat_min": 25.9, "lat_max": 26.5, "lon_min": 91.4, "lon_max": 92.0},
        "context": "Annual flood zone — Brahmaputra river",
    },
    "uttarakhand": {
        "id":      "uttarakhand",
        "name":    "Chamoli, Uttarakhand",
        "lat":     30.4,
        "lon":     79.3,
        "bbox":    {"lat_min": 30.1, "lat_max": 30.7, "lon_min": 79.0, "lon_max": 79.6},
        "context": "Glacier burst risk — Himalayan region",
    },
}

# ── Request / response schemas ────────────────────────────────────────────────

class AnalysisRequest(BaseModel):
    region_name: str
    lat:         float
    lon:         float
    bbox:        dict

class PDFRequest(BaseModel):
    analysis: dict


# ── Middleware: log every request with timing ────────────────────────────────

@app.middleware("http")
async def _request_logger(request: Request, call_next):
    t0       = time.time()
    response = await call_next(request)
    elapsed  = int((time.time() - t0) * 1000)
    try:
        log_request(
            event            = "http_request",
            region           = "—",
            user_ip          = request.client.host if request.client else "unknown",
            endpoint         = str(request.url.path),
            method           = request.method,
            status_code      = response.status_code,
            response_time_ms = elapsed,
        )
    except Exception:
        pass
    return response


# ── Routes ────────────────────────────────────────────────────────────────────

@app.get("/")
async def root():
    return {
        "name":    "DisasterMind",
        "version": "1.0.0",
        "status":  "operational",
        "tagline": "Autonomous Disaster Response Intelligence for India",
    }


@app.get("/health")
async def health():
    # Check whether ONNX models are loaded
    flood_loaded    = predictor._flood_session    is not None
    severity_loaded = predictor._severity_session is not None

    if flood_loaded and severity_loaded:
        ml_status = "loaded"
    elif not flood_loaded and not severity_loaded:
        ml_status = "fallback"
    else:
        ml_status = "partial"

    groq_key = os.getenv("GROQ_API_KEY", "")
    return {
        "status":     "healthy",
        "ml_models":  ml_status,
        "groq":       "connected" if groq_key else "key_missing",
        "firms":      "key_set"   if os.getenv("NASA_FIRMS_KEY") else "key_missing",
        "gee":        "project_set" if os.getenv("GEE_PROJECT")  else "key_missing",
    }


@app.post("/analyze")
@limiter.limit("10/minute")
async def analyze(request: Request, body: AnalysisRequest):
    """
    Main analysis endpoint — runs the full autonomous pipeline.
    Rate limited: 10 requests/minute per IP.
    """
    t0      = time.time()
    user_ip = request.client.host if request.client else "unknown"

    try:
        result = await run_disaster_analysis(
            region_name = body.region_name,
            lat         = body.lat,
            lon         = body.lon,
            bbox        = body.bbox,
        )
        elapsed = int((time.time() - t0) * 1000)
        log_request(
            event            = "analysis_complete",
            region           = body.region_name,
            user_ip          = user_ip,
            risk_level       = result.get("situation_report", {}).get("risk_level", "UNKNOWN"),
            response_time_ms = elapsed,
        )
        return result

    except Exception as e:
        log_error("analysis_failed", e, region=body.region_name, user_ip=user_ip)
        raise HTTPException(status_code=500, detail=f"Analysis pipeline failed: {str(e)}")


@app.get("/demo/{region}")
async def demo(region: str):
    """
    Return pre-cached analysis for demo regions.
    Regions: wayanad | assam | uttarakhand
    """
    region = region.lower().strip()
    cache_file = DEMO_CACHE_DIR / f"{region}.json"

    if not cache_file.exists():
        raise HTTPException(
            status_code = 404,
            detail      = f"No demo cache found for '{region}'. Run demo_cache.py first.",
        )
    try:
        with open(cache_file, "r", encoding="utf-8") as f:
            data = json.load(f)
        return data
    except Exception as e:
        log_error("demo_cache_read_failed", e, region=region)
        raise HTTPException(status_code=500, detail="Failed to read demo cache")


@app.get("/regions")
async def regions():
    """Return the 3 preset disaster regions for the demo map."""
    return list(PRESET_REGIONS.values())


@app.post("/report/pdf")
async def report_pdf(body: PDFRequest):
    """
    Generate a PDF situation report from analysis JSON.
    Returns application/pdf binary stream.
    """
    try:
        pdf_bytes = generate_pdf(body.analysis)
        region    = body.analysis.get("region", "disastermind_report")
        filename  = f"DisasterMind_{region.replace(' ', '_').replace(',', '')}.pdf"

        return StreamingResponse(
            iter([pdf_bytes]),
            media_type = "application/pdf",
            headers    = {"Content-Disposition": f'attachment; filename="{filename}"'},
        )
    except Exception as e:
        log_error("pdf_generation_failed", e)
        raise HTTPException(status_code=500, detail=f"PDF generation failed: {str(e)}")
