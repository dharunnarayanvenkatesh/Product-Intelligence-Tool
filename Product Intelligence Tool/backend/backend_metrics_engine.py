from sqlalchemy import select, func, and_, distinct
from datetime import datetime, timedelta
from database import Event, Metric

class MetricsEngine:
    def __init__(self, db):
        self.db = db
    
    async def compute_dau(self):
        """Compute Daily Active Users"""
        today = datetime.utcnow().replace(hour=0, minute=0, second=0, microsecond=0)
        yesterday = today - timedelta(days=1)
        
        # Count distinct users for yesterday
        result = await self.db.execute(
            select(func.count(distinct(Event.user_id)))
            .where(and_(
                Event.timestamp >= yesterday,
                Event.timestamp < today
            ))
        )
        dau_count = result.scalar()
        
        metric = Metric(
            metric_name="dau",
            metric_type="engagement",
            value=float(dau_count),
            date=yesterday,
            metadata={"period": "daily"}
        )
        self.db.add(metric)
    
    async def compute_wau(self):
        """Compute Weekly Active Users"""
        today = datetime.utcnow().replace(hour=0, minute=0, second=0, microsecond=0)
        week_ago = today - timedelta(days=7)
        
        result = await self.db.execute(
            select(func.count(distinct(Event.user_id)))
            .where(and_(
                Event.timestamp >= week_ago,
                Event.timestamp < today
            ))
        )
        wau_count = result.scalar()
        
        metric = Metric(
            metric_name="wau",
            metric_type="engagement",
            value=float(wau_count),
            date=today,
            metadata={"period": "weekly"}
        )
        self.db.add(metric)
    
    async def compute_mau(self):
        """Compute Monthly Active Users"""
        today = datetime.utcnow().replace(hour=0, minute=0, second=0, microsecond=0)
        month_ago = today - timedelta(days=30)
        
        result = await self.db.execute(
            select(func.count(distinct(Event.user_id)))
            .where(and_(
                Event.timestamp >= month_ago,
                Event.timestamp < today
            ))
        )
        mau_count = result.scalar()
        
        metric = Metric(
            metric_name="mau",
            metric_type="engagement",
            value=float(mau_count),
            date=today,
            metadata={"period": "monthly"}
        )
        self.db.add(metric)
    
    async def compute_retention(self):
        """Compute D1, D7, D30 retention"""
        cohort_date = datetime.utcnow().replace(hour=0, minute=0, second=0, microsecond=0) - timedelta(days=30)
        
        # Get cohort users
        result = await self.db.execute(
            select(distinct(Event.user_id))
            .where(and_(
                Event.timestamp >= cohort_date,
                Event.timestamp < cohort_date + timedelta(days=1)
            ))
        )
        cohort_users = {row[0] for row in result.fetchall()}
        cohort_size = len(cohort_users)
        
        if cohort_size == 0:
            return
        
        # D1 retention
        d1_date = cohort_date + timedelta(days=1)
        result = await self.db.execute(
            select(distinct(Event.user_id))
            .where(and_(
                Event.user_id.in_(cohort_users),
                Event.timestamp >= d1_date,
                Event.timestamp < d1_date + timedelta(days=1)
            ))
        )
        d1_users = len(result.fetchall())
        d1_retention = (d1_users / cohort_size) * 100
        
        metric = Metric(
            metric_name="retention_d1",
            metric_type="retention",
            value=d1_retention,
            date=cohort_date,
            metadata={"cohort_size": cohort_size, "retained_users": d1_users}
        )
        self.db.add(metric)
        
        # D7 retention
        d7_date = cohort_date + timedelta(days=7)
        result = await self.db.execute(
            select(distinct(Event.user_id))
            .where(and_(
                Event.user_id.in_(cohort_users),
                Event.timestamp >= d7_date,
                Event.timestamp < d7_date + timedelta(days=1)
            ))
        )
        d7_users = len(result.fetchall())
        d7_retention = (d7_users / cohort_size) * 100
        
        metric = Metric(
            metric_name="retention_d7",
            metric_type="retention",
            value=d7_retention,
            date=cohort_date,
            metadata={"cohort_size": cohort_size, "retained_users": d7_users}
        )
        self.db.add(metric)
        
        # D30 retention
        d30_date = cohort_date + timedelta(days=30)
        result = await self.db.execute(
            select(distinct(Event.user_id))
            .where(and_(
                Event.user_id.in_(cohort_users),
                Event.timestamp >= d30_date,
                Event.timestamp < d30_date + timedelta(days=1)
            ))
        )
        d30_users = len(result.fetchall())
        d30_retention = (d30_users / cohort_size) * 100
        
        metric = Metric(
            metric_name="retention_d30",
            metric_type="retention",
            value=d30_retention,
            date=cohort_date,
            metadata={"cohort_size": cohort_size, "retained_users": d30_users}
        )
        self.db.add(metric)
    
    async def compute_feature_adoption(self):
        """Compute feature adoption rates"""
        today = datetime.utcnow().replace(hour=0, minute=0, second=0, microsecond=0)
        week_ago = today - timedelta(days=7)
        
        # Get all unique event names as features
        result = await self.db.execute(
            select(distinct(Event.event_name))
            .where(and_(
                Event.timestamp >= week_ago,
                Event.timestamp < today
            ))
        )
        features = [row[0] for row in result.fetchall()]
        
        # Get total users
        result = await self.db.execute(
            select(func.count(distinct(Event.user_id)))
            .where(and_(
                Event.timestamp >= week_ago,
                Event.timestamp < today
            ))
        )
        total_users = result.scalar()
        
        if total_users == 0:
            return
        
        for feature in features:
            # Count users who used this feature
            result = await self.db.execute(
                select(func.count(distinct(Event.user_id)))
                .where(and_(
                    Event.event_name == feature,
                    Event.timestamp >= week_ago,
                    Event.timestamp < today
                ))
            )
            feature_users = result.scalar()
            adoption_rate = (feature_users / total_users) * 100
            
            metric = Metric(
                metric_name=f"adoption_{feature}",
                metric_type="feature_adoption",
                value=adoption_rate,
                date=today,
                metadata={
                    "feature": feature,
                    "users": feature_users,
                    "total_users": total_users
                }
            )
            self.db.add(metric)
    
    async def compute_funnels(self):
        """Compute conversion funnels"""
        today = datetime.utcnow().replace(hour=0, minute=0, second=0, microsecond=0)
        week_ago = today - timedelta(days=7)
        
        # Example funnel: signup -> onboarding -> first_action
        funnel_steps = ["signup", "onboarding_complete", "first_action"]
        
        # Get users at each step
        step_users = {}
        for step in funnel_steps:
            result = await self.db.execute(
                select(distinct(Event.user_id))
                .where(and_(
                    Event.event_name == step,
                    Event.timestamp >= week_ago,
                    Event.timestamp < today
                ))
            )
            step_users[step] = {row[0] for row in result.fetchall()}
        
        if len(step_users.get(funnel_steps[0], set())) == 0:
            return
        
        # Calculate conversion rates
        base_count = len(step_users[funnel_steps[0]])
        conversions = {}
        
        for i, step in enumerate(funnel_steps):
            if i == 0:
                conversions[step] = 100.0
            else:
                prev_users = step_users[funnel_steps[i-1]]
                curr_users = step_users[step]
                converted = len(curr_users & prev_users)
                conversions[step] = (converted / len(prev_users)) * 100 if len(prev_users) > 0 else 0
        
        metric = Metric(
            metric_name="funnel_signup_to_action",
            metric_type="funnel",
            value=conversions[funnel_steps[-1]],
            date=today,
            metadata={
                "steps": funnel_steps,
                "conversions": conversions,
                "base_users": base_count
            }
        )
        self.db.add(metric)