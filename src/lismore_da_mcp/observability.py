"""Logging, with applicant data structurally excluded.

The server had none at all, so on the public deployment there was no record of
what was asked, what failed, or whether the rate limiter was engaging — any user
report of a bad answer was unfalsifiable.

The hard constraint is that this server handles other people's personal
information. `fill_see_pdf` and `preview_see_form` take an applicant's name,
street address and lot/DP; `generate_see_draft` takes the same. Those must never
reach a log line, on a public unauthenticated service whose logs go to a
third-party platform.

That is enforced by shape rather than by discipline: `record_tool_call()` accepts
a tool *name*, a duration and an outcome. It has no parameter that could carry an
argument value, so there is no call site where someone could pass one by
accident. Argument *names* are safe and are not logged either, since knowing a
caller supplied `applicant_name` adds nothing.

tests/test_observability.py asserts that a call carrying a fake name, address and
lot/DP produces log output containing none of them.
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
# Deliberately no parameter that can carry an argument value. See module
# docstring: this is what stops applicant data being logged, rather than a
# convention that a future edit could quietly break.

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

    The client IP is deliberately not logged. It is personal information, the
    endpoint is public and unauthenticated, and Render's proxy already records
    request-level detail — so carrying it into application logs adds retention
    risk without adding much. What matters here is that the limiter engaged at
    all, which is the signal for tuning it or moving to a real edge limiter.
    """
    logger.warning(
        f"event=rate_limited max_requests={max_requests} window_seconds={window_seconds:g}"
    )


def record_index_state(status: str, segments: int | None = None) -> None:
    """Whether the search index is present.

    Worth a line because a missing index is invisible from outside: search still
    answers, just via a full scan at roughly a thousand times the cost. That
    exact failure shipped to production once and was only caught by timing the
    endpoint.
    """
    message = f"event=search_index status={status}"
    if segments is not None:
        message += f" segments={segments}"
    logger.info(message)


def record_document_error(operation: str, document: str, error_type: str, detail: str) -> None:
    """A document could not be read.

    Document names are safe to log — they are public planning documents, not
    applicant material. Before logging existed, a PDF that failed to open was
    indistinguishable from one containing no matches, so a silently unsearchable
    document could sit there indefinitely.
    """
    logger.error(
        f"event=document_error operation={operation} document={document} "
        f"error_type={error_type} detail={detail!r}"
    )


def record_startup(transport: str) -> None:
    logger.info(f"event=startup transport={transport}")
