from sqlalchemy.exc import IntegrityError

from app.database.db import db
from app.models.compass_recommendation import CompassRecommendation


class CompassRepository:
    """Data access layer for persistent Forge Compass recommendations."""

    def get_all(self, status=None, priority=None, category=None, include_inactive=True):
        query = CompassRecommendation.query
        if status:
            query = query.filter_by(status=status)
        if priority:
            query = query.filter_by(priority=priority)
        if category:
            query = query.filter_by(category=category)
        if not include_inactive:
            query = query.filter_by(is_active=True)
        return query.order_by(CompassRecommendation.id.asc()).all()

    def get_by_id(self, rec_id):
        return db.session.get(CompassRecommendation, rec_id)

    def get_by_dedupe_key(self, dedupe_key):
        return CompassRecommendation.query.filter_by(dedupe_key=dedupe_key).first()

    def add(self, recommendation):
        db.session.add(recommendation)

    def commit(self):
        try:
            db.session.commit()
        except IntegrityError:
            db.session.rollback()
            raise
        except Exception:
            db.session.rollback()
            raise
