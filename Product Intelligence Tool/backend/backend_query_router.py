from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_, func
from pydantic import BaseModel
from datetime import datetime, timedelta

from database import get_db, Event, Metric, Insight
from llm.client import LLMClient

router = APIRouter()

class QueryRequest(BaseModel):
    question: str

@router.post("/ask")
async def ask_question(
    request: QueryRequest,
    db: AsyncSession = Depends(get_db)
):
    # Get recent metrics
    result = await db.execute(
        select(Metric).order_by(Metric.computed_at.desc()).limit(100)
    )
    recent_metrics = result.scalars().all()
    
    # Get recent insights
    result = await db.execute(
        select(Insight).where(Insight.resolved == "pending")
        .order_by(Insight.detected_at.desc()).limit(20)
    )
    recent_insights = result.scalars().all()
    
    # Build context
    context = {
        "metrics": [
            {
                "name": m.metric_name,
                "type": m.metric_type,
                "value": m.value,
                "date": m.date.isoformat(),
                "metadata": m.metadata
            }
            for m in recent_metrics
        ],
        "insights": [
            {
                "type": i.insight_type,
                "severity": i.severity,
                "title": i.title,
                "data": i.data
            }
            for i in recent_insights
        ]
    }
    
    # Query LLM
    llm_client = LLMClient()
    answer = await llm_client.query(request.question, context)
    
    return {"question": request.question, "answer": answer}

@router.post("/analyze")
async def analyze_metric(
    metric_name: str,
    db: AsyncSession = Depends(get_db)
):
    # Get metric history
    result = await db.execute(
        select(Metric).where(Metric.metric_name == metric_name)
        .order_by(Metric.date.desc()).limit(30)
    )
    metrics = result.scalars().all()
    
    if not metrics:
        return {"error": "Metric not found"}
    
    # Get related insights
    result = await db.execute(
        select(Insight).where(
            Insight.data["metric_name"].astext == metric_name
        ).order_by(Insight.detected_at.desc()).limit(10)
    )
    insights = result.scalars().all()
    
    context = {
        "metric_name": metric_name,
        "history": [
            {"date": m.date.isoformat(), "value": m.value, "metadata": m.metadata}
            for m in metrics
        ],
        "insights": [
            {"type": i.insight_type, "title": i.title, "data": i.data}
            for i in insights
        ]
    }
    
    llm_client = LLMClient()
    analysis = await llm_client.analyze_metric(context)
    
    return {"metric": metric_name, "analysis": analysis}