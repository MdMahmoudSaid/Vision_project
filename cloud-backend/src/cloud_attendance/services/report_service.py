import json
from collections import defaultdict
from datetime import date, datetime, time, timedelta, timezone
from typing import List, Optional

from sqlalchemy import select
from sqlalchemy.orm import Session

from cloud_attendance.models import Correction, CorrectionAction, SyncedAttendanceEvent, SyncedEmployee, SyncIngestLog, utcnow
from cloud_attendance.models.synced_verification_attempt import SyncedAttendanceType
from cloud_attendance.schemas.report import (
    CompletenessStatus,
    Report,
    ReportGranularity,
    ReportPeriod,
    ReportRow,
    ReportScope,
    ReportScopeType,
)


class EffectiveEvent:
    """A synced attendance event as it should be displayed after applying
    any corrections — either the raw synced event, an event whose time/type
    was corrected, or a synthetic event created entirely by a
    add_arrival/add_departure correction. Never mutates the underlying
    SyncedAttendanceEvent or Correction rows; this is a read-time view only."""

    def __init__(self, id: str, employee_id: str, type: str, timestamp: datetime, is_corrected: bool = False):
        self.id = id
        self.employee_id = employee_id
        self.type = type
        self.timestamp = timestamp
        self.is_corrected = is_corrected


def _as_utc(ts: datetime) -> datetime:
    return ts if ts.tzinfo is not None else ts.replace(tzinfo=timezone.utc)


def _get_last_sync_time(db: Session) -> Optional[datetime]:
    last_log = db.scalars(
        select(SyncIngestLog).where(SyncIngestLog.success == True).order_by(SyncIngestLog.timestamp.desc()).limit(1)  # noqa: E712
    ).first()
    if not last_log:
        return None
    return _as_utc(last_log.timestamp)


def _build_effective_events(
    db: Session, employee_ids: list[str], start_dt: datetime, end_dt: datetime
) -> list[EffectiveEvent]:
    """Combines raw synced events with corrections: the latest correction per
    attendance_event_id wins (a chain of corrections is still fully visible
    in the audit trail via GET /attendance/corrections/{employee_id} — this
    function only decides what reports/history should *display*)."""
    event_query = select(SyncedAttendanceEvent).where(
        SyncedAttendanceEvent.timestamp >= start_dt,
        SyncedAttendanceEvent.timestamp <= end_dt,
    )
    if employee_ids:
        event_query = event_query.where(SyncedAttendanceEvent.employee_id.in_(employee_ids))
    raw_events = db.scalars(event_query).all()

    corrections_query = select(Correction).order_by(Correction.performed_at.asc())
    if employee_ids:
        corrections_query = corrections_query.where(Correction.employee_id.in_(employee_ids))
    corrections = db.scalars(corrections_query).all()

    # Latest correct_time/change_type correction per attendance_event_id wins.
    latest_edit_by_event_id: dict[str, Correction] = {}
    add_corrections: list[Correction] = []
    for correction in corrections:
        if correction.action in (CorrectionAction.CORRECT_TIME, CorrectionAction.CHANGE_TYPE):
            if correction.attendance_event_id:
                latest_edit_by_event_id[correction.attendance_event_id] = correction
        else:
            add_corrections.append(correction)

    effective: list[EffectiveEvent] = []
    for evt in raw_events:
        edit = latest_edit_by_event_id.get(evt.id)
        if edit is None:
            effective.append(EffectiveEvent(evt.id, evt.employee_id, evt.type.value, _as_utc(evt.timestamp)))
            continue
        new_value = json.loads(edit.new_value)
        if edit.action == CorrectionAction.CORRECT_TIME:
            timestamp = _as_utc(datetime.fromisoformat(new_value["timestamp"]))
            evt_type = evt.type.value
        else:  # CHANGE_TYPE
            timestamp = _as_utc(evt.timestamp)
            evt_type = new_value["type"]
        effective.append(EffectiveEvent(evt.id, evt.employee_id, evt_type, timestamp, is_corrected=True))

    for correction in add_corrections:
        new_value = json.loads(correction.new_value)
        timestamp = _as_utc(datetime.fromisoformat(new_value["timestamp"]))
        if not (start_dt <= timestamp <= end_dt):
            continue
        evt_type = "arrival" if correction.action == CorrectionAction.ADD_ARRIVAL else "departure"
        effective.append(
            EffectiveEvent(f"correction:{correction.id}", correction.employee_id, evt_type, timestamp, is_corrected=True)
        )

    return effective


def generate_report(
    db: Session,
    granularity: ReportGranularity,
    date_from: date,
    date_to: date,
    employee_id: Optional[str] = None,
) -> Report:
    scope_type = ReportScopeType.EMPLOYEE if employee_id else ReportScopeType.ORGANIZATION
    scope = ReportScope(type=scope_type, employee_id=employee_id)
    period = ReportPeriod(granularity=granularity, date_from=date_from, date_to=date_to)

    last_sync = _get_last_sync_time(db)
    period_end_dt = datetime.combine(date_to, time(23, 59, 59, 999999)).replace(tzinfo=timezone.utc)
    may_be_incomplete = last_sync is None or period_end_dt > last_sync

    emp_query = select(SyncedEmployee).where(SyncedEmployee.active == True)  # noqa: E712
    if employee_id:
        emp_query = emp_query.where(SyncedEmployee.id == employee_id)
    employees = db.scalars(emp_query).all()
    emp_map = {e.id: e for e in employees}

    start_dt = datetime.combine(date_from, time.min).replace(tzinfo=timezone.utc)
    end_dt = period_end_dt

    scoped_employee_ids = [employee_id] if employee_id else list(emp_map.keys())
    effective_events = _build_effective_events(db, scoped_employee_ids, start_dt, end_dt)

    # emp_date_events[emp_id][date_str] = [EffectiveEvent, ...]
    emp_date_events: dict[str, dict[str, list[EffectiveEvent]]] = defaultdict(lambda: defaultdict(list))
    for evt in effective_events:
        if evt.employee_id in emp_map:
            emp_date_events[evt.employee_id][evt.timestamp.date().isoformat()].append(evt)

    rows: List[ReportRow] = []
    days = (date_to - date_from).days
    target_dates = [date_from + timedelta(days=i) for i in range(days + 1)]

    for emp in employees:
        for target_date in target_dates:
            d_str = target_date.isoformat()
            day_events = emp_date_events[emp.id].get(d_str, [])

            # Pairing: first arrival of the day, last departure of the day.
            arrival_time = None
            departure_time = None
            day_corrected = False

            for evt in sorted(day_events, key=lambda e: e.timestamp):
                if evt.is_corrected:
                    day_corrected = True
                if evt.type == "arrival" and arrival_time is None:
                    arrival_time = evt.timestamp
                elif evt.type == "departure":
                    departure_time = evt.timestamp

            if arrival_time and departure_time:
                completeness = CompletenessStatus.COMPLETE
            elif arrival_time and not departure_time:
                completeness = CompletenessStatus.MISSING_DEPARTURE
            elif not arrival_time and departure_time:
                completeness = CompletenessStatus.MISSING_ARRIVAL
            else:
                completeness = CompletenessStatus.NO_RECORD

            worked_duration_minutes = None
            if arrival_time and departure_time and departure_time > arrival_time:
                delta = departure_time - arrival_time
                worked_duration_minutes = int(delta.total_seconds() / 60)

            rows.append(
                ReportRow(
                    employee_id=emp.id,
                    employee_name=emp.full_name,
                    date=target_date,
                    arrival_time=arrival_time,
                    departure_time=departure_time,
                    worked_duration_minutes=worked_duration_minutes,
                    completeness=completeness,
                    corrected=day_corrected,
                )
            )

    return Report(
        scope=scope,
        period=period,
        rows=rows,
        generated_at=utcnow(),
        may_be_incomplete=may_be_incomplete,
    )
