# app/core/scheduler.py
from datetime import datetime, date
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger

from app.reports.multi_session_report import generate_multi_session_report

scheduler: AsyncIOScheduler | None = None
_last_daily_report: dict | None = None


def get_latest_cached_report() -> dict | None:
    return _last_daily_report


def _run_daily_report_job():
    global _last_daily_report
    today = date.today().isoformat()
    _last_daily_report = generate_multi_session_report(today)


def init_scheduler():
    global scheduler
    if scheduler is not None:
        return scheduler

    scheduler = AsyncIOScheduler(timezone="UTC")
    # Run every 5 minutes just as example (you can change to hourly / per-session)
    scheduler.add_job(_run_daily_report_job, CronTrigger(minute="*/5"))
    scheduler.start()
    return scheduler
