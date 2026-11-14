"""
FastAPI Backend for Apex-Metal GPU Inference Service
======================================================

RESTful API for model inference with MemoryOS tier management.
"""

import logging
from typing import Optional
from datetime import datetime

from fastapi import FastAPI, HTTPException, BackgroundTasks
from fastapi.responses import JSONResponse
from pydantic import BaseModel

from apex_core.engine import InferenceEngine, MemoryTierConfig, InferenceMetrics

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)

# Initialize FastAPI app
app = FastAPI(
    title="Apex-Metal GPU Inference Service",
    description="GPU-aware inference engine with MemoryOS tier management",
    version="0.2.0"
)

# Global inference engine (initialized on startup)
inference_engine: Optional[InferenceEngine] = None


# Request/Response Models
class HealthResponse(BaseModel):
    status: str
    timestamp: str
    gpu_available: bool
    models_loaded: int


class LoadModelRequest(BaseModel):
    model_id: str
    tier: str = "hot"  # hot, warm, cold
    quantize: bool = False


class LoadModelResponse(BaseModel):
    success: bool
    model_id: str
    tier: str
    message: str


class InferenceRequest(BaseModel):
    model_id: str
    prompt: str
    max_tokens: int = 256
    temperature: float = 0.7


class InferenceResponse(BaseModel):
    model_id: str
    prompt: str
    generated_text: str
    latency_ms: float
    throughput_tokens_per_sec: float
    gpu_memory_mb: float
    tier: str


class TierStatusResponse(BaseModel):
    hot_gpu: dict
    warm_cpu: dict
    cold_nvme: dict
    persistent_mram: dict


class MetricsResponse(BaseModel):
    total_inferences: int
    avg_latency_ms: float
    avg_throughput_tokens_per_sec: float
    avg_gpu_memory_mb: float
    latest_inference: Optional[str]


# Startup/Shutdown Events
@app.on_event("startup")
async def startup_event():
    """Initialize inference engine on app startup."""
    global inference_engine
    
    logger.info("Initializing Apex-Metal inference engine...")
    
    config = MemoryTierConfig(
        hot_max_gb=20.0,
        warm_max_gb=64.0,
        cold_path="/nvme/checkpoints",
        persistent_path="~/.cache/mrameda"
    )
    
    inference_engine = InferenceEngine(config=config)
    logger.info("Inference engine initialized successfully")


@app.on_event("shutdown")
async def shutdown_event():
    """Cleanup on app shutdown."""
    global inference_engine
    
    if inference_engine:
        logger.info("Shutting down inference engine...")
        # Cleanup: save registry, clear cache, etc.
        inference_engine.router.save_registry()
        logger.info("Inference engine shutdown complete")


# Health and Status Endpoints
@app.get("/health", response_model=HealthResponse)
async def health_check():
    """
    Health check endpoint.
    
    Returns status of the inference service and GPU availability.
    """
    if not inference_engine:
        return HealthResponse(
            status="unhealthy",
            timestamp=datetime.now().isoformat(),
            gpu_available=False,
            models_loaded=0
        )
    
    return HealthResponse(
        status="healthy",
        timestamp=datetime.now().isoformat(),
        gpu_available=inference_engine.gpu_manager.device_count > 0,
        models_loaded=len(inference_engine.loaded_models)
    )


@app.get("/")
async def root():
    """Root endpoint with service information."""
    return {
        "service": "Apex-Metal GPU Inference Engine",
        "version": "0.2.0",
        "status": "healthy",
        "endpoints": {
            "health": "/health",
            "models/load": "POST /models/load",
            "inference": "POST /inference",
            "status": "GET /status",
            "metrics": "GET /metrics"
        }
    }


# Model Management Endpoints
@app.post("/models/load", response_model=LoadModelResponse)
async def load_model(request: LoadModelRequest):
    """
    Load a model to specified memory tier.
    
    Args:
        model_id: HuggingFace model ID or local path
        tier: Target memory tier (hot/warm/cold)
        quantize: Whether to use quantization for efficiency
    
    Returns:
        Status of model loading operation
    """
    if not inference_engine:
        raise HTTPException(status_code=503, detail="Inference engine not initialized")
    
    try:
        success = await inference_engine.load_model(
            model_id=request.model_id,
            tier=request.tier,
            quantize=request.quantize
        )
        
        if success:
            return LoadModelResponse(
                success=True,
                model_id=request.model_id,
                tier=request.tier,
                message=f"Model {request.model_id} loaded successfully on {request.tier} tier"
            )
        else:
            raise HTTPException(
                status_code=500,
                detail=f"Failed to load model {request.model_id}"
            )
    
    except Exception as e:
        logger.error(f"Error loading model: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# Inference Endpoints
@app.post("/inference", response_model=InferenceResponse)
async def run_inference(request: InferenceRequest):
    """
    Run inference on loaded model.
    
    Args:
        model_id: ID of previously loaded model
        prompt: Input prompt for generation
        max_tokens: Maximum tokens to generate
        temperature: Sampling temperature (0-2.0)
    
    Returns:
        Generated text and performance metrics
    """
    if not inference_engine:
        raise HTTPException(status_code=503, detail="Inference engine not initialized")
    
    if request.model_id not in inference_engine.loaded_models:
        raise HTTPException(
            status_code=404,
            detail=f"Model {request.model_id} not loaded. Use /models/load first."
        )
    
    try:
        generated_text, metrics = await inference_engine.inference(
            model_id=request.model_id,
            prompt=request.prompt,
            max_tokens=request.max_tokens,
            temperature=request.temperature
        )
        
        return InferenceResponse(
            model_id=request.model_id,
            prompt=request.prompt,
            generated_text=generated_text,
            latency_ms=metrics.latency_ms,
            throughput_tokens_per_sec=metrics.throughput_tokens_per_sec,
            gpu_memory_mb=metrics.gpu_memory_mb,
            tier=metrics.tier
        )
    
    except Exception as e:
        logger.error(f"Inference error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# Status and Monitoring Endpoints
@app.get("/status", response_model=TierStatusResponse)
async def get_status():
    """
    Get current status of all memory tiers.
    
    Returns information about:
    - GPU VRAM (hot tier)
    - CPU RAM (warm tier)
    - NVMe storage (cold tier)
    - Persistent cache (MRAM tier)
    """
    if not inference_engine:
        raise HTTPException(status_code=503, detail="Inference engine not initialized")
    
    status = inference_engine.get_tier_status()
    return TierStatusResponse(**status)


@app.get("/metrics", response_model=MetricsResponse)
async def get_metrics():
    """
    Get inference performance metrics.
    
    Returns aggregated statistics from recent inference operations.
    """
    if not inference_engine:
        raise HTTPException(status_code=503, detail="Inference engine not initialized")
    
    summary = inference_engine.get_metrics_summary()
    
    if "error" in summary:
        raise HTTPException(status_code=400, detail=summary["error"])
    
    return MetricsResponse(**summary)


@app.get("/models")
async def list_models():
    """List all loaded models and their status."""
    if not inference_engine:
        raise HTTPException(status_code=503, detail="Inference engine not initialized")
    
    models_info = []
    for model_id, info in inference_engine.loaded_models.items():
        models_info.append({
            "model_id": model_id,
            "tier": info["tier"],
            "device": info["device"],
            "loaded_at": info["loaded_at"].isoformat(),
            "quantized": info["quantized"]
        })
    
    return {
        "total_loaded": len(models_info),
        "models": models_info
    }


# Error Handlers
@app.exception_handler(Exception)
async def general_exception_handler(request, exc):
    """Global exception handler."""
    logger.error(f"Unhandled exception: {exc}")
    return JSONResponse(
        status_code=500,
        content={"detail": "Internal server error"}
    )


if __name__ == "__main__":
    import uvicorn
    
    logger.info("Starting Apex-Metal FastAPI server...")
    uvicorn.run(
        app,
        host="0.0.0.0",
        port=8000,
        log_level="info"
    )
