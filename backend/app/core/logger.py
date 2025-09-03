from __future__ import annotations

import logging


def get_logger(name: str | None = None) -> logging.Logger:
    """Return a module-level logger.

    Assumes root logger is configured in app.main. This helper avoids duplicating
    basicConfig calls and keeps consistent formatting/handlers.
    """
    return logging.getLogger(name)
