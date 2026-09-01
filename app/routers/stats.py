from datetime import date, timedelta

from fastapi import APIRouter, Depends
from sqlalchemy import case, func
from sqlalchemy.orm import Session

from app.database import get_db
from app.envelope import ok
from app.models import CallLog, Patient

router = APIRouter(prefix="/stats", tags=["stats"])


@router.get("")
def get_stats(db: Session = Depends(get_db)):
    active = db.query(Patient).filter(Patient.deleted_at.is_(None))
    total = active.count()
    with_insurance = active.filter(Patient.insurance_provider.isnot(None)).count()
    with_emergency = active.filter(Patient.emergency_contact_name.isnot(None)).count()
    week_ago = date.today() - timedelta(days=7)
    new_this_week = active.filter(func.date(Patient.created_at) >= week_ago).count()

    def grouped(column):
        rows = (
            db.query(column, func.count(Patient.patient_id))
            .filter(Patient.deleted_at.is_(None))
            .group_by(column)
            .order_by(func.count(Patient.patient_id).desc())
            .all()
        )
        return [{"label": value or "Unknown", "value": count} for value, count in rows]

    start = date.today() - timedelta(days=29)
    day_rows = (
        db.query(func.date(Patient.created_at), func.count(Patient.patient_id))
        .filter(Patient.deleted_at.is_(None), func.date(Patient.created_at) >= start)
        .group_by(func.date(Patient.created_at))
        .all()
    )
    counts_by_day = {str(day): count for day, count in day_rows}
    registrations = []
    for offset in range(30):
        day = start + timedelta(days=offset)
        registrations.append({"label": day.isoformat(), "value": counts_by_day.get(str(day), 0)})

    recent_calls = (
        db.query(CallLog).order_by(CallLog.created_at.desc()).limit(10).all()
    )

    return ok(
        {
            "kpis": {
                "total_patients": total,
                "new_this_week": new_this_week,
                "with_insurance": with_insurance,
                "with_emergency_contact": with_emergency,
                "recent_calls": db.query(func.count(CallLog.id)).scalar() or 0,
            },
            "by_state": grouped(Patient.state),
            "by_sex": grouped(Patient.sex),
            "by_language": grouped(Patient.preferred_language),
            "by_insurance": grouped(
                case((Patient.insurance_provider.is_(None), "Uninsured / not provided"), else_=Patient.insurance_provider)
            ),
            "registrations": registrations,
            "recent_calls": [
                {
                    "id": row.id,
                    "patient_id": row.patient_id,
                    "caller_number": row.caller_number,
                    "outcome": row.outcome,
                    "created_at": row.created_at.isoformat() if row.created_at else None,
                }
                for row in recent_calls
            ],
        }
    )
