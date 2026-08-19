"""Observable provider fallback router for evidence data."""
from __future__ import annotations

from dataclasses import dataclass, field
import logging
from typing import Any, Iterable

logger = logging.getLogger(__name__)


@dataclass
class RoutedResult:
    data: Any
    source: str
    available: bool = True
    status: str = "ok"
    warnings: list[str] = field(default_factory=list)


class ProviderRouter:
    """Call providers in order and preserve failure/degradation metadata."""

    def __init__(self, providers: Iterable[Any]):
        self.providers = list(providers)
        self.quality: dict[str, str] = {}
        self.warnings: list[str] = []

    def call(self, method: str, *args, **kwargs) -> RoutedResult:
        errors: list[str] = []
        for provider in self.providers:
            source = provider.__class__.__name__
            func = getattr(provider, method, None)
            if func is None:
                continue
            try:
                data = func(*args, **kwargs)
                if data is None or getattr(data, "empty", False):
                    message = f"{source}.{method}: empty response"
                    errors.append(message)
                    self.quality[method] = "unavailable"
                    continue
                status = "ok" if not errors else "fallback"
                warning_list = list(errors)
                self.quality[method] = status
                if warning_list:
                    self.warnings.extend(warning_list)
                    logger.warning("%s", " | ".join(warning_list))
                return RoutedResult(data, source, True, status, warning_list)
            except (RuntimeError, OSError, ValueError, TypeError) as exc:
                message = f"{source}.{method}: {type(exc).__name__}: {exc}"
                errors.append(message)
                logger.warning("provider unavailable: %s", message)
        joined = " | ".join(errors) if errors else "no compatible provider"
        self.quality[method] = "unavailable"
        self.warnings.extend(errors)
        return RoutedResult(
            data=None,
            source="none",
            available=False,
            status="unavailable",
            warnings=errors or [joined],
        )

    def quality_report(self) -> dict[str, str]:
        return dict(self.quality)
