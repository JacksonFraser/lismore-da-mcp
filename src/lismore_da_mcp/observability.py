"""Logging, with applicant data structurally excluded.

Several tools take an applicant's name, address and lot/DP, and the public
deployment's logs go to a third-party platform. So `record_tool_call()` accepts
only a tool name, a duration and an outcome: it has no parameter that could carry
an argument value. tests/test_observability.py checks that none leaks.
"""

import logging
import os
import time
from contextlib import contextmanager

LOGGER_NAME = "lismore_da_mcp"

logger = logging.getLogger(LOGGER_NAME)


def configure_logging() -> logging.Logger:
    """Set up logging once, at process start.

    Level comes from LISMORE_LOG_LEVEL so the deployed service can be turned up
    without a code change. Handlers are only added if nothing else has configured
    the root logger, so this does not fight a host that already has.
    """
    level_name = os.environ.get("LISMORE_LOG_LEVEL", "INFO").upper()
    level = getattr(logging, level_name, logging.INFO)
    logger.setLevel(level)

    if not logger.handlers and not logging.getLogger().handlers:
        handler = logging.StreamHandler()
        handler.setFormatter(
            logging.Formatter("%(asctime)s %(levelname)s %(name)s %(message)s")
        )
        logger.addHandler(handler)

    logger.propagate = True
    return logger


# --- tool calls -----------------------------------------------------------
#
# Deliberately no parameter that can carry an argument value (see module docstring).

OUTCOME_OK = "ok"
OUTCOME_INVALID_ARGUMENTS = "invalid_arguments"
OUTCOME_ERROR = "error"


def record_tool_call(
    tool_name: str,
    duration_ms: float,
    outcome: str,
    error_type: str | None = None,
) -> None:
    """One line per tool call: what was called, how long, how it went."""
    message = f"tool={tool_name} outcome={outcome} duration_ms={duration_ms:.1f}"
    if error_type:
        message += f" error_type={error_type}"
    if outcome == OUTCOME_ERROR:
        logger.error(message)
    elif outcome == OUTCOME_INVALID_ARGUMENTS:
        logger.warning(message)
    else:
        logger.info(message)


@contextmanager
def timed_tool_call(tool_name: str):
    """Time a tool call and log its outcome, including when it raises.

    Yields a one-item list used to mark the outcome; defaults to error, so a
    handler that raises past this point is still recorded rather than vanishing.
    """
    started = time.perf_counter()
    outcome = [OUTCOME_ERROR]
    try:
        yield outcome
    except Exception as exc:
        record_tool_call(
            tool_name,
            (time.perf_counter() - started) * 1000,
            OUTCOME_ERROR,
            type(exc).__name__,
        )
        raise
    else:
        record_tool_call(tool_name, (time.perf_counter() - started) * 1000, outcome[0])


# --- operational events ---------------------------------------------------


def record_rate_limited(window_seconds: float, max_requests: int) -> None:
    """A request was rejected by the limiter.

    The client IP is personal information and Render's proxy already records it,
    so it is not logged here.
    """
    logger.warning(
        f"event=rate_limited max_requests={max_requests} window_seconds={window_seconds:g}"
    )


def record_index_state(status: str, segments: int | None = None) -> None:
    """Whether the search index is present.

    A missing index is invisible from outside — search still answers, via a much
    slower full scan — so it is logged at startup.
    """
    message = f"event=search_index status={status}"
    if segments is not None:
        message += f" segments={segments}"
    logger.info(message)


def record_document_error(operation: str, document: str, error_type: str, detail: str) -> None:
    """A document could not be read.

    Otherwise an unreadable PDF looks the same as one with no matches. Document
    names are public planning documents, so they are safe to log.
    """
    logger.error(
        f"event=document_error operation={operation} document={document} "
        f"error_type={error_type} detail={detail!r}"
    )


def record_startup(transport: str) -> None:
    logger.info(f"event=startup transport={transport}")
