from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, and_
from datetime import datetime, timedelta
from typing import Optional

from database import get_db, Metric

router = APIRouter()

@router.get("/dau")
async def get_dau(
    start_date: Optional[str] = Query(None),
    end_date: Optional[str] = Query(None),
    db: AsyncSession = Depends(get_db)
):
    query = select(Metric).where(Metric.metric_name == "dau")
    
    if start_date:
        query = query.where(Metric.date >= datetime.fromisoformat(start_date))
    if end_date:
        query = query.where(Metric.date <= datetime.fromisoformat(end_date))
    
    query = query.order_by(Metric.date.desc()).limit(30)
    result = await db.execute(query)
    metrics = result.scalars().all()
    
    return {
        "metrics": [
            {
                "date": m.date.isoformat(),
                "value": m.value,
                "metadata": m.metadata
            }
            for m in metrics
        ]
    }

@router.get("/retention")
async def get_retention(
    cohort_date: Optional[str] = Query(None),
    db: AsyncSession = Depends(get_db)
):
    query = select(Metric).where(Metric.metric_type == "retention")
    
    if cohort_date:
        query = query.where(Metric.date == datetime.fromisoformat(cohort_date))
    
    query = query.order_by(Metric.date.desc()).limit(100)
    result = await db.execute(query)
    metrics = result.scalars().all()
    
    return {
        "metrics": [
            {
                "date": m.date.isoformat(),
                "metric_name": m.metric_name,
                "value": m.value,
                "metadata": m.metadata
            }
            for m in metrics
        ]
    }

@router.get("/feature-adoption")
async def get_feature_adoption(
    feature: Optional[str] = Query(None),
    db: AsyncSession = Depends(get_db)
):
    query = select(Metric).where(Metric.metric_type == "feature_adoption")
    
    if feature:
        query = query.where(Metric.metadata["feature"].astext == feature)
    
    query = query.order_by(Metric.date.desc()).limit(50)
    result = await db.execute(query)
    metrics = result.scalars().all()
    
    return {
        "metrics": [
            {
                "date": m.date.isoformat(),
                "feature": m.metadata.get("feature"),
                "value": m.value,
                "metadata": m.metadata
            }
            for m in metrics
        ]
    }

@router.get("/funnel")
async def get_funnel(
    funnel_name: str = Query(...),
    db: AsyncSession = Depends(get_db)
):
    query = select(Metric).where(
        and_(
            Metric.metric_type == "funnel",
            Metric.metric_name == funnel_name
        )
    ).order_by(Metric.date.desc()).limit(30)
    
    result = await db.execute(query)
    metrics = result.scalars().all()
    
    return {
        "metrics": [
            {
                "date": m.date.isoformat(),
                "value": m.value,
                "metadata": m.metadata
            }
            for m in metrics
        ]
    }

@router.get("/all")
async def get_all_metrics(
    metric_type: Optional[str] = Query(None),
    limit: int = Query(100),
    db: AsyncSession = Depends(get_db)
):
    query = select(Metric)
    
    if metric_type:
        query = query.where(Metric.metric_type == metric_type)
    
    query = query.order_by(Metric.computed_at.desc()).limit(limit)
    result = await db.execute(query)
    metrics = result.scalars().all()
    
    return {
        "metrics": [
            {
                "id": m.id,
                "metric_name": m.metric_name,
                "metric_type": m.metric_type,
                "value": m.value,
                "date": m.date.isoformat(),
                "metadata": m.metadata,
                "computed_at": m.computed_at.isoformat()
            }
            for m in metrics
        ]
    }