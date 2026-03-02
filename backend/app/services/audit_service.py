import json
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from app.models.audit import AuditLog
class AuditService:
    def __init__(self, db: AsyncSession):
        self.db = db
    async def log(self, user_id, action, entity_type, entity_id=None,
                  old_values=None, new_values=None, ip_address=None):
        entry = AuditLog(
            user_id=str(user_id),
            action=action,
            entity_type=entity_type,
            entity_id=str(entity_id) if entity_id else None,
            old_values=json.dumps(old_values) if old_values else None,
            new_values=json.dumps(new_values) if new_values else None,
            ip_address=ip_address,
        )
        self.db.add(entry)
        await self.db.flush()
        return entry
    async def list_logs(self, page=1, per_page=50, action=None, entity_type=None, user_id=None):
        query = select(AuditLog)
        count_query = select(func.count()).select_from(AuditLog)
        if action:
            query = query.where(AuditLog.action == action)
            count_query = count_query.where(AuditLog.action == action)
        if entity_type:
            query = query.where(AuditLog.entity_type == entity_type)
            count_query = count_query.where(AuditLog.entity_type == entity_type)
        if user_id:
            query = query.where(AuditLog.user_id == str(user_id))
            count_query = count_query.where(AuditLog.user_id == str(user_id))
        total = (await self.db.execute(count_query)).scalar() or 0
        query = query.offset((page - 1) * per_page).limit(per_page).order_by(AuditLog.created_at.desc())
        result = await self.db.execute(query)
        logs = result.scalars().all()
        return list(logs), total