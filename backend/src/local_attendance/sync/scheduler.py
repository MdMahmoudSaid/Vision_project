import asyncio
import logging

from local_attendance.config import get_settings
from local_attendance.database import SessionLocal
from local_attendance.sync.client import run_sync_batch

logger = logging.getLogger(__name__)

_MAX_BACKOFF_MULTIPLIER = 8  # caps retry wait at 8x the configured interval


async def sync_loop() -> None:
    settings = get_settings()
    interval = settings.sync_interval_seconds

    logger.info("Starting sync scheduler (interval: %d seconds)", interval)

    consecutive_failures = 0
    while True:
        succeeded = True
        try:
            with SessionLocal() as db:
                succeeded = await run_sync_batch(db)
        except asyncio.CancelledError:
            logger.info("Sync scheduler cancelled")
            break
        except Exception as exc:
            logger.exception("Unexpected error in sync scheduler: %s", exc)
            succeeded = False

        if succeeded:
            consecutive_failures = 0
            wait_seconds = interval
        else:
            consecutive_failures += 1
            backoff_multiplier = min(2 ** consecutive_failures, _MAX_BACKOFF_MULTIPLIER)
            wait_seconds = interval * backoff_multiplier
            logger.warning(
                "Sync attempt failed (%d consecutive); backing off to %d seconds",
                consecutive_failures,
                wait_seconds,
            )

        try:
            await asyncio.sleep(wait_seconds)
        except asyncio.CancelledError:
            logger.info("Sync scheduler cancelled during sleep")
            break
