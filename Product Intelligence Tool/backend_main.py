from fastapi import FastAPI, HTTPException, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
import uvicorn
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.interval import IntervalTrigger

from database import init_db
from routers import ingestion, metrics, insights, query
from jobs import metric_computation_job, detection_job

scheduler = AsyncIOScheduler()

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    await init_db()
    scheduler.add_job(
        metric_computation_job,
        IntervalTrigger(hours=1),
        id="compute_metrics",
        replace_existing=True
    )
    scheduler.add_job(
        detection_job,
        IntervalTrigger(hours=6),
        id="detect_anomalies",
        replace_existing=True
    )
    scheduler.start()
    yield
    # Shutdown
    scheduler.shutdown()

app = FastAPI(title="CXM Product Intelligence", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(ingestion.router, prefix="/api/ingestion", tags=["ingestion"])
app.include_router(metrics.router, prefix="/api/metrics", tags=["metrics"])
app.include_router(insights.router, prefix="/api/insights", tags=["insights"])
app.include_router(query.router, prefix="/api/query", tags=["query"])

@app.get("/")
async def root():
    return {"status": "running", "service": "cxm-intelligence"}

@app.get("/health")
async def health():
    return {"status": "healthy"}

if __name__ == "__main__":
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)