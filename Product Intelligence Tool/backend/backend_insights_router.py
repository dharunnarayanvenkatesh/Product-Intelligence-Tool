from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_
from typing import Optional
from datetime import datetime

from database import get_db, Insight

router = APIRouter()

@router.get("/")
async def get_insights(
    insight_type: Optional[str] = Query(None),
    severity: Optional[str] = Query(None),
    resolved: Optional[str] = Query(None),
    limit: int = Query(50),
    db: AsyncSession = Depends(get_db)
):
    query = select(Insight)
    
    filters = []
    if insight_type:
        filters.append(Insight.insight_type == insight_type)
    if severity:
        filters.append(Insight.severity == severity)
    if resolved:
        filters.append(Insight.resolved == resolved)
    
    if filters:
        query = query.where(and_(*filters))
    
    query = query.order_by(Insight.detected_at.desc()).limit(limit)
    result = await db.execute(query)
    insights = result.scalars().all()
    
    return {
        "insights": [
            {
                "id": i.id,
                "insight_type": i.insight_type,
                "severity": i.severity,
                "title": i.title,
                "detected_at": i.detected_at.isoformat(),
                "data": i.data,
                "llm_explanation": i.llm_explanation,
                "resolved": i.resolved
            }
            for i in insights
        ]
    }

@router.get("/{insight_id}")
async def get_insight(
    insight_id: int,
    db: AsyncSession = Depends(get_db)
):
    result = await db.execute(select(Insight).where(Insight.id == insight_id))
    insight = result.scalar_one_or_none()
    
    if not insight:
        return {"error": "Insight not found"}
    
    return {
        "id": insight.id,
        "insight_type": insight.insight_type,
        "severity": insight.severity,
        "title": insight.title,
        "detected_at": insight.detected_at.isoformat(),
        "data": insight.data,
        "llm_explanation": insight.llm_explanation,
        "resolved": insight.resolved,
        "created_at": insight.created_at.isoformat()
    }

@router.post("/{insight_id}/resolve")
async def resolve_insight(
    insight_id: int,
    db: AsyncSession = Depends(get_db)
):
    result = await db.execute(select(Insight).where(Insight.id == insight_id))
    insight = result.scalar_one_or_none()
    
    if not insight:
        return {"error": "Insight not found"}
    
    insight.resolved = "resolved"
    await db.commit()
    
    return {"status": "resolved"}

@router.get("/summary/stats")
async def get_insight_stats(db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Insight))
    all_insights = result.scalars().all()
    
    stats = {
        "total": len(all_insights),
        "by_type": {},
        "by_severity": {},
        "by_status": {}
    }
    
    for insight in all_insights:
        stats["by_type"][insight.insight_type] = stats["by_type"].get(insight.insight_type, 0) + 1
        stats["by_severity"][insight.severity] = stats["by_severity"].get(insight.severity, 0) + 1
        stats["by_status"][insight.resolved] = stats["by_status"].get(insight.resolved, 0) + 1
    
    return stats