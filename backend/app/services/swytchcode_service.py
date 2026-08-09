"""
Swytchcode execution service.

Swytchcode is a CLI execution kernel that sits between this backend and the
real Gmail / Notion / Jira / GitHub / Resend APIs. It is NOT a Python SDK —
per the Swytchcode docs (docs.swytchcode.com) the integration surface is:

    swytchcode init                          # creates .swytchcode/ + tooling.json
    swytchcode add <spec> <canonical_id>      # pulls a "wrekenfile" (integration
                                               # spec: methods, endpoints, schemas)
                                               # and registers it in tooling.json
    swytchcode info <canonical_id>            # inspect a registered tool's schema
    swytchcode exec <canonical_id> --json      # execute, reading JSON input from stdin,
                                               # returns structured JSON output

tooling.json is the trusted-tool policy file (like a lockfile) — every
canonical_id this backend is allowed to call must already be registered
there. This service deliberately does NOT invent canonical IDs: it reads
them from `tooling.json` / `SWYTCHCODE_TOOLS` below, and if a tool isn't
registered yet it fails loudly rather than guessing an endpoint name.

IMPORTANT — before switching DEMO_MODE off:
  1. Run `swytchcode login` locally.
  2. Run `swytchcode init` in the backend/ directory.
  3. For each integration, run:
         swytchcode add gmail   gmail.<action>
         swytchcode add notion  notion.<action>
         swytchcode add jira    jira.<action>
         swytchcode add github  github.<action>
         swytchcode add resend  resend.<action>
     using `swytchcode search <query>` / the Swytchcode dashboard to find
     the *real* canonical IDs for "search messages", "search pages",
     "search issues", "create issue", "send email" etc. for your account's
     connected apps — these vary by what's enabled in your Swytchcode
     workspace and are NOT hardcoded here.
  4. Fill in the resulting canonical IDs in `tooling.json` at the project
     root (see the placeholders already there) — this service reads them
     from there via `load_tool_map()`.
"""

from __future__ import annotations

import asyncio
import json
import time
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Optional

from app.core.config import get_settings

TOOLING_JSON_PATH = Path(__file__).resolve().parents[3] / "tooling.json"


@dataclass
class SwytchcodeResult:
    ok: bool
    canonical_id: str
    output: dict[str, Any] = field(default_factory=dict)
    error: Optional[str] = None
    duration_ms: int = 0
    mode: str = "sandbox"


class SwytchcodeNotConfiguredError(RuntimeError):
    pass


class SwytchcodeToolNotRegisteredError(RuntimeError):
    pass


def load_tool_map() -> dict[str, str]:
    """
    Reads tooling.json and returns {logical_action: canonical_id}.
    Logical actions are our own internal names (e.g. "gmail.search"),
    canonical IDs are whatever Swytchcode actually registered for them
    (e.g. "gmail.messages.search") once you've run `swytchcode add`.
    """
    if not TOOLING_JSON_PATH.exists():
        return {}
    try:
        data = json.loads(TOOLING_JSON_PATH.read_text())
    except (json.JSONDecodeError, OSError):
        return {}
    return data.get("resolve_ai_action_map", {})


class SwytchcodeService:
    """
    Thin, auditable wrapper around `swytchcode exec`. Every call:
      - validates the tool is registered in tooling.json before running
      - runs the CLI as a subprocess with a timeout
      - captures stdout/stderr and timing for the audit trail
      - falls back to a clearly-labeled demo response when DEMO_MODE is on
        or no Swytchcode API key is configured, so the rest of the app
        (and the buildathon demo) works with zero external credentials.
    """

    def __init__(self) -> None:
        self.settings = get_settings()
        self.tool_map = load_tool_map()

    @property
    def live_mode(self) -> bool:
        return not self.settings.DEMO_MODE and self.settings.swytchcode_configured

    def _canonical_id_for(self, logical_action: str) -> Optional[str]:
        return self.tool_map.get(logical_action)

    async def exec(
        self,
        logical_action: str,
        payload: dict[str, Any],
        *,
        demo_fallback: Optional[dict[str, Any]] = None,
    ) -> SwytchcodeResult:
        """
        Execute a Swytchcode tool by our internal logical action name
        (e.g. "notion.search"). Resolves it to a canonical_id via
        tooling.json, then shells out to `swytchcode exec`.
        """
        start = time.perf_counter()

        if not self.live_mode:
            # Demo / not-yet-connected path — never silently pretend a real
            # call succeeded; the response is explicitly marked as demo data.
            await asyncio.sleep(0.05)  # keeps the activity timeline feeling real-time
            duration_ms = int((time.perf_counter() - start) * 1000)
            return SwytchcodeResult(
                ok=True,
                canonical_id=self._canonical_id_for(logical_action) or f"(demo) {logical_action}",
                output={"demo": True, **(demo_fallback or {})},
                duration_ms=duration_ms,
                mode="demo",
            )

        canonical_id = self._canonical_id_for(logical_action)
        if not canonical_id:
            raise SwytchcodeToolNotRegisteredError(
                f"'{logical_action}' has no canonical_id in tooling.json. "
                f"Run `swytchcode add <spec> <canonical_id>` for this integration "
                f"and add the mapping under resolve_ai_action_map."
            )

        try:
            proc = await asyncio.create_subprocess_exec(
                self.settings.SWYTCHCODE_BIN,
                "exec",
                canonical_id,
                "--json",
                stdin=asyncio.subprocess.PIPE,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
            )
            stdin_bytes = json.dumps(payload).encode()
            try:
                stdout, stderr = await asyncio.wait_for(
                    proc.communicate(stdin_bytes),
                    timeout=self.settings.SWYTCHCODE_TIMEOUT_SECONDS,
                )
            except asyncio.TimeoutError:
                proc.kill()
                duration_ms = int((time.perf_counter() - start) * 1000)
                return SwytchcodeResult(
                    ok=False,
                    canonical_id=canonical_id,
                    error=f"swytchcode exec timed out after {self.settings.SWYTCHCODE_TIMEOUT_SECONDS}s",
                    duration_ms=duration_ms,
                    mode=self.settings.SWYTCHCODE_MODE,
                )

            duration_ms = int((time.perf_counter() - start) * 1000)

            if proc.returncode != 0:
                return SwytchcodeResult(
                    ok=False,
                    canonical_id=canonical_id,
                    error=(stderr.decode(errors="replace") or "swytchcode exec failed")[:2000],
                    duration_ms=duration_ms,
                    mode=self.settings.SWYTCHCODE_MODE,
                )

            try:
                output = json.loads(stdout.decode())
            except json.JSONDecodeError:
                output = {"raw": stdout.decode(errors="replace")}

            return SwytchcodeResult(
                ok=True,
                canonical_id=canonical_id,
                output=output,
                duration_ms=duration_ms,
                mode=self.settings.SWYTCHCODE_MODE,
            )

        except FileNotFoundError:
            duration_ms = int((time.perf_counter() - start) * 1000)
            return SwytchcodeResult(
                ok=False,
                canonical_id=canonical_id,
                error=(
                    f"'{self.settings.SWYTCHCODE_BIN}' not found on PATH. "
                    f"Install it (see README) or set SWYTCHCODE_BIN."
                ),
                duration_ms=duration_ms,
                mode=self.settings.SWYTCHCODE_MODE,
            )
        except Exception as exc:  # noqa: BLE001 — surfaced to audit trail, not swallowed
            duration_ms = int((time.perf_counter() - start) * 1000)
            return SwytchcodeResult(
                ok=False,
                canonical_id=canonical_id,
                error=str(exc)[:2000],
                duration_ms=duration_ms,
                mode=self.settings.SWYTCHCODE_MODE,
            )


swytchcode_service = SwytchcodeService()
