import structlog
import logging
import sys

structlog.configure(
    processors=[
        structlog.processors.TimeStamper(fmt="iso"),
        structlog.processors.add_log_level,
        structlog.processors.JSONRenderer()
    ],
    context_class=dict,
    logger_factory=structlog.PrintLoggerFactory(file=sys.stdout),
    wrapper_class=structlog.make_filtering_bound_logger(logging.INFO),
    cache_logger_on_first_use=True,
)

logger = structlog.get_logger()

def log_request(event: str, region: str, user_ip: str, **kwargs):
    """Logs a request event in JSON format."""
    logger.info(event, region=region, user_ip=user_ip, **kwargs)

def log_error(event: str, error: str, **kwargs):
    """Logs an error event in JSON format."""
    logger.error(event, error=error, **kwargs)
