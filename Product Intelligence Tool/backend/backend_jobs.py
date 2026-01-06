from sqlalchemy import select, func, and_, distinct
from datetime import datetime, timedelta
from database import AsyncSessionLocal, Event, Metric, Insight
from engines.metrics import MetricsEngine
from engines.detection import DetectionEngine
from llm.client import LLMClient

async def metric_computation_job():
    """Compute all metrics periodically"""
    async with AsyncSessionLocal() as db:
        engine = MetricsEngine(db)
        
        # Compute DAU/WAU/MAU
        await engine.compute_dau()
        await engine.compute_wau()
        await engine.compute_mau()
        
        # Compute retention
        await engine.compute_retention()
        
        # Compute feature adoption
        await engine.compute_feature_adoption()
        
        # Compute funnels
        await engine.compute_funnels()
        
        await db.commit()

async def detection_job():
    """Run anomaly detection and generate insights"""
    async with AsyncSessionLocal() as db:
        detection_engine = DetectionEngine(db)
        llm_client = LLMClient()
        
        # Detect metric regressions
        regressions = await detection_engine.detect_regressions()
        
        # Detect anomalies
        anomalies = await detection_engine.detect_anomalies()
        
        # Detect feature decay
        decay = await detection_engine.detect_feature_decay()
        
        # Detect retention erosion
        retention_issues = await detection_engine.detect_retention_erosion()
        
        # Combine all detections
        all_detections = regressions + anomalies + decay + retention_issues
        
        # Generate insights with LLM explanations
        for detection in all_detections:
            explanation = await llm_client.explain_insight(detection)
            
            insight = Insight(
                insight_type=detection["type"],
                severity=detection["severity"],
                title=detection["title"],
                detected_at=datetime.utcnow(),
                data=detection["data"],
                llm_explanation=explanation,
                resolved="pending"
            )
            db.add(insight)
        
        await db.commit()