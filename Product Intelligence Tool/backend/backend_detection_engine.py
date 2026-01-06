from sqlalchemy import select, and_
from datetime import datetime, timedelta
from database import Metric
import numpy as np

class DetectionEngine:
    def __init__(self, db):
        self.db = db
    
    async def detect_regressions(self):
        """Detect week-over-week and day-over-day regressions"""
        detections = []
        today = datetime.utcnow().replace(hour=0, minute=0, second=0, microsecond=0)
        
        # Get key metrics
        key_metrics = ["dau", "wau", "mau", "retention_d1", "retention_d7"]
        
        for metric_name in key_metrics:
            # Get last 14 days
            result = await self.db.execute(
                select(Metric)
                .where(and_(
                    Metric.metric_name == metric_name,
                    Metric.date >= today - timedelta(days=14)
                ))
                .order_by(Metric.date.desc())
            )
            metrics = result.scalars().all()
            
            if len(metrics) < 2:
                continue
            
            # Check WoW regression
            if len(metrics) >= 7:
                this_week_avg = np.mean([m.value for m in metrics[:7]])
                last_week_avg = np.mean([m.value for m in metrics[7:14]]) if len(metrics) >= 14 else this_week_avg
                
                if last_week_avg > 0:
                    change_pct = ((this_week_avg - last_week_avg) / last_week_avg) * 100
                    
                    if change_pct < -10:  # 10% regression threshold
                        detections.append({
                            "type": "regression",
                            "severity": "high" if change_pct < -20 else "medium",
                            "title": f"{metric_name} dropped {abs(change_pct):.1f}% WoW",
                            "data": {
                                "metric_name": metric_name,
                                "change_pct": change_pct,
                                "current_value": this_week_avg,
                                "previous_value": last_week_avg,
                                "period": "week"
                            }
                        })
            
            # Check DoD regression
            if len(metrics) >= 2:
                today_value = metrics[0].value
                yesterday_value = metrics[1].value
                
                if yesterday_value > 0:
                    change_pct = ((today_value - yesterday_value) / yesterday_value) * 100
                    
                    if change_pct < -15:  # 15% regression threshold for daily
                        detections.append({
                            "type": "regression",
                            "severity": "critical" if change_pct < -30 else "high",
                            "title": f"{metric_name} dropped {abs(change_pct):.1f}% DoD",
                            "data": {
                                "metric_name": metric_name,
                                "change_pct": change_pct,
                                "current_value": today_value,
                                "previous_value": yesterday_value,
                                "period": "day"
                            }
                        })
        
        return detections
    
    async def detect_anomalies(self):
        """Detect statistical anomalies using z-score"""
        detections = []
        today = datetime.utcnow().replace(hour=0, minute=0, second=0, microsecond=0)
        
        # Get all metric types
        result = await self.db.execute(
            select(Metric.metric_name)
            .where(Metric.date >= today - timedelta(days=30))
            .distinct()
        )
        metric_names = [row[0] for row in result.fetchall()]
        
        for metric_name in metric_names:
            result = await self.db.execute(
                select(Metric)
                .where(and_(
                    Metric.metric_name == metric_name,
                    Metric.date >= today - timedelta(days=30)
                ))
                .order_by(Metric.date.desc())
            )
            metrics = result.scalars().all()
            
            if len(metrics) < 7:
                continue
            
            values = [m.value for m in metrics]
            mean = np.mean(values)
            std = np.std(values)
            
            if std == 0:
                continue
            
            # Check latest value
            latest_value = values[0]
            z_score = (latest_value - mean) / std
            
            if abs(z_score) > 2.5:  # 2.5 std deviations
                detections.append({
                    "type": "anomaly",
                    "severity": "high" if abs(z_score) > 3 else "medium",
                    "title": f"{metric_name} anomaly detected",
                    "data": {
                        "metric_name": metric_name,
                        "current_value": latest_value,
                        "mean": mean,
                        "std": std,
                        "z_score": z_score,
                        "direction": "spike" if z_score > 0 else "drop"
                    }
                })
        
        return detections
    
    async def detect_feature_decay(self):
        """Detect declining feature usage"""
        detections = []
        today = datetime.utcnow().replace(hour=0, minute=0, second=0, microsecond=0)
        
        result = await self.db.execute(
            select(Metric)
            .where(and_(
                Metric.metric_type == "feature_adoption",
                Metric.date >= today - timedelta(days=30)
            ))
        )
        metrics = result.scalars().all()
        
        # Group by feature
        feature_metrics = {}
        for m in metrics:
            feature = m.metadata.get("feature")
            if feature not in feature_metrics:
                feature_metrics[feature] = []
            feature_metrics[feature].append(m)
        
        for feature, feature_data in feature_metrics.items():
            if len(feature_data) < 4:
                continue
            
            # Sort by date
            feature_data.sort(key=lambda x: x.date, reverse=True)
            
            # Check trend
            recent_values = [m.value for m in feature_data[:4]]
            
            # Simple trend check: all declining
            if all(recent_values[i] > recent_values[i+1] for i in range(len(recent_values)-1)):
                total_decline = recent_values[0] - recent_values[-1]
                
                if total_decline > 15:  # 15% decline
                    detections.append({
                        "type": "feature_decay",
                        "severity": "medium",
                        "title": f"Feature '{feature}' usage declining",
                        "data": {
                            "feature": feature,
                            "decline_pct": total_decline,
                            "current_adoption": recent_values[0],
                            "trend": recent_values
                        }
                    })
        
        return detections
    
    async def detect_retention_erosion(self):
        """Detect retention cohort issues"""
        detections = []
        today = datetime.utcnow().replace(hour=0, minute=0, second=0, microsecond=0)
        
        retention_metrics = ["retention_d1", "retention_d7", "retention_d30"]
        
        for metric_name in retention_metrics:
            result = await self.db.execute(
                select(Metric)
                .where(and_(
                    Metric.metric_name == metric_name,
                    Metric.date >= today - timedelta(days=60)
                ))
                .order_by(Metric.date.desc())
            )
            metrics = result.scalars().all()
            
            if len(metrics) < 4:
                continue
            
            # Check if retention is declining
            recent = [m.value for m in metrics[:4]]
            avg_recent = np.mean(recent)
            
            if len(metrics) >= 8:
                older = [m.value for m in metrics[4:8]]
                avg_older = np.mean(older)
                
                if avg_older > 0:
                    change = ((avg_recent - avg_older) / avg_older) * 100
                    
                    if change < -10:
                        detections.append({
                            "type": "retention_erosion",
                            "severity": "high" if change < -20 else "medium",
                            "title": f"{metric_name} eroding",
                            "data": {
                                "metric_name": metric_name,
                                "change_pct": change,
                                "recent_avg": avg_recent,
                                "older_avg": avg_older
                            }
                        })
        
        return detections