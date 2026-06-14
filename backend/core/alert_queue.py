"""
DisasterMind — Event-Driven Alert Queue
Provides an asynchronous in-memory queue for Telegram alerts so that slow
external APIs do not block the main fast pipeline.
"""

import asyncio
from core.alerter import send_alert, send_national_summary

# The global in-memory queue
_alert_queue = asyncio.Queue()

async def enqueue_cell_alert(kwargs: dict):
    """Push a cell-level threat alert to the background queue."""
    await _alert_queue.put({"type": "cell_alert", "payload": kwargs})

async def enqueue_national_summary(kwargs: dict):
    """Push a national summary alert to the background queue."""
    await _alert_queue.put({"type": "national_summary", "payload": kwargs})

async def alert_worker():
    """
    Background worker that continuously pulls from the queue and sends alerts.
    Implements a simple retry mechanism for failed deliveries.
    """
    print("[AlertQueue] Background worker started")
    while True:
        try:
            task = await _alert_queue.get()
            
            task_type = task["type"]
            payload = task["payload"]
            retries = task.get("retries", 0)

            success = False
            try:
                if task_type == "cell_alert":
                    success = await send_alert(**payload)
                elif task_type == "national_summary":
                    success = await send_national_summary(**payload)
            except Exception as e:
                print(f"[AlertQueue] Exception sending {task_type}: {e}")

            if not success and retries < 3:
                # Re-queue with exponential backoff (simplified: just wait and re-queue)
                await asyncio.sleep(2 ** retries)
                task["retries"] = retries + 1
                await _alert_queue.put(task)
                print(f"[AlertQueue] Re-queued {task_type} (attempt {retries + 1}/3)")
            elif not success:
                print(f"[AlertQueue] Dropped {task_type} after 3 failed attempts")

            _alert_queue.task_done()
        except asyncio.CancelledError:
            print("[AlertQueue] Worker cancelled")
            break
        except Exception as e:
            print(f"[AlertQueue] Worker loop error: {e}")
            await asyncio.sleep(5)
