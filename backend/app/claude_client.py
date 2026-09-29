from __future__ import annotations

import base64
import logging

import anthropic

from .config import Settings
from .models import Fix, ViolationGroup

logger = logging.getLogger(__name__)

SYSTEM_PROMPT = """You are an accessibility engineer helping a developer fix a \
WCAG issue that an automated scanner (axe-core) found on their live page.

For every issue you are given:
- Explain in 2-4 plain-English sentences who is affected and why it matters. \
Name the actual assistive technology or disability affected (e.g. "screen \
reader users", "people navigating by keyboard", "people with low vision"), \
not just "accessibility". Avoid jargon.
- Propose a fix as a single replacement for the flagged element's outerHTML. \
Prefer plain, native HTML semantics (a <button>, a <label>, an alt attribute) \
over ARIA attributes — only reach for ARIA when there is no native HTML \
element or attribute that solves the problem. Keep the fix minimal: change \
only what's needed to resolve this specific issue, keep existing classes, \
ids, data attributes, and other functionality intact.
- The fix must be a complete, well-formed HTML fragment that could directly \
replace the original element in the DOM.

You always respond by calling the propose_fix tool. Never claim the page is \
now "compliant" — you're proposing one fix for one issue among possibly \
others a human still needs to check (keyboard navigation, screen reader \
testing, zoom/reflow)."""

PROPOSE_FIX_TOOL = {
    "name": "propose_fix",
    "description": "Explain an accessibility issue and propose a code fix for it.",
    "input_schema": {
        "type": "object",
        "properties": {
            "explanation": {
                "type": "string",
                "description": "2-4 sentence plain-English explanation of who is affected and why.",
            },
            "new_html": {
                "type": "string",
                "description": "Full replacement outerHTML for the flagged element.",
            },
            "note": {
                "type": "string",
                "description": "One short sentence on what changed and why, if not obvious from the diff.",
            },
        },
        "required": ["explanation", "new_html"],
    },
}

# Rough per-million-token estimates in USD, used only for the soft in-scan
# spend guard — not a substitute for a real billing cap in your Anthropic
# console. Update if pricing changes.
PRICE_PER_MTOK_INPUT = 3.0
PRICE_PER_MTOK_OUTPUT = 15.0


class BudgetExceededError(RuntimeError):
    pass


class ClaudeClient:
    def __init__(self, settings: Settings, api_key_override: str | None = None):
        """api_key_override lets a caller bring their own Anthropic key for a
        single scan (BYOK). It takes priority over the server's own
        ANTHROPIC_API_KEY, if any, so the server never has to pay for a
        scan someone else's key is covering. Never logged, never stored
        anywhere beyond this in-memory client for the life of one scan."""
        self.settings = settings
        self._client: anthropic.AsyncAnthropic | None = None
        key = api_key_override or settings.anthropic_api_key
        if key:
            self._client = anthropic.AsyncAnthropic(api_key=key)
        self.key_supplied = bool(key)
        self.auth_failed = False
        self.api_errors = 0
        self.issues_explained = 0
        self.estimated_spend_usd = 0.0
        self.calls_made = 0
        self.calls_skipped_budget = 0

    def status(self) -> tuple[str, str | None]:
        """One report-level AI status instead of an error on every issue.
        Any issue Claude didn't cover silently falls back to the built-in
        guidance, which is always present."""
        if not self.key_supplied:
            return "off", None
        if self.auth_failed:
            return (
                "error",
                "Anthropic didn't accept that API key, so this report uses the "
                "built-in guidance. Check the key and scan again for tailored fixes.",
            )
        if self.issues_explained == 0 and self.api_errors:
            return (
                "error",
                "Anthropic's API returned errors for this scan, so this report "
                "uses the built-in guidance. Try again in a minute.",
            )
        notes = []
        if self.calls_skipped_budget:
            notes.append(
                f"{self.calls_skipped_budget} lower-priority issue(s) use built-in "
                "guidance because this scan reached its AI spend cap."
            )
        if self.api_errors:
            notes.append(
                f"{self.api_errors} issue(s) use built-in guidance because "
                "Anthropic's API returned an error for them."
            )
        return "on", " ".join(notes) or None

    @property
    def available(self) -> bool:
        return self._client is not None

    def _record_usage(self, usage) -> None:
        cost = (
            (usage.input_tokens / 1_000_000) * PRICE_PER_MTOK_INPUT
            + (usage.output_tokens / 1_000_000) * PRICE_PER_MTOK_OUTPUT
        )
        self.estimated_spend_usd += cost

    def _budget_left(self) -> bool:
        return self.estimated_spend_usd < self.settings.max_scan_spend_usd

    async def explain_and_fix(self, group: ViolationGroup) -> ViolationGroup:
        if not self.available:
            return group

        if not self._budget_left():
            self.calls_skipped_budget += 1
            return group

        representative = group.nodes[0] if group.nodes else None
        node_desc = (
            f"Element HTML:\n{representative.html}\n\n"
            f"axe failure summary:\n{representative.failure_summary}"
            if representative
            else "No specific element HTML was captured for this rule."
        )

        user_prompt = (
            f"WCAG rule: {group.rule_id}\n"
            f"WCAG success criteria: {', '.join(group.wcag_tags) or 'n/a'}\n"
            f"Impact: {group.impact}\n"
            f"Rule description: {group.description}\n"
            f"axe help text: {group.help_text}\n"
            f"This appears {group.total_node_count} time(s) on the page.\n\n"
            f"{node_desc}"
        )

        try:
            self.calls_made += 1
            response = await self._client.messages.create(
                model=self.settings.claude_model,
                max_tokens=1024,
                system=[
                    {
                        "type": "text",
                        "text": SYSTEM_PROMPT,
                        "cache_control": {"type": "ephemeral"},
                    }
                ],
                tools=[PROPOSE_FIX_TOOL],
                tool_choice={"type": "tool", "name": "propose_fix"},
                messages=[{"role": "user", "content": user_prompt}],
            )
            self._record_usage(response.usage)

            tool_use = next(
                (b for b in response.content if b.type == "tool_use"), None
            )
            if tool_use is None:
                self.api_errors += 1
                group.explanation_error = "AI response did not include a proposed fix."
                return group

            payload = tool_use.input
            group.explanation = payload.get("explanation", "").strip() or None
            if representative and payload.get("new_html"):
                group.fix = Fix(
                    old_html=representative.html,
                    new_html=payload["new_html"].strip(),
                    note=payload.get("note"),
                )
            self.issues_explained += 1
        except (anthropic.AuthenticationError, anthropic.PermissionDeniedError) as exc:
            # A bad key fails identically for every issue; stop calling
            # Anthropic for the rest of this scan instead of repeating it.
            logger.warning("Anthropic rejected the supplied key: %s", type(exc).__name__)
            self.auth_failed = True
            self._client = None
        except anthropic.APIError as exc:
            logger.warning("Claude API error for rule %s: %s", group.rule_id, exc)
            self.api_errors += 1
            group.explanation_error = f"AI explanation failed: {exc}"
        except Exception as exc:  # noqa: BLE001 - surface to report, don't crash scan
            logger.exception("Unexpected error explaining rule %s", group.rule_id)
            self.api_errors += 1
            group.explanation_error = f"AI explanation failed: {exc}"

        return group

    async def suggest_alt_text(self, image_png: bytes, context: str) -> str | None:
        if not self.available or not self._budget_left():
            return None
        try:
            self.calls_made += 1
            response = await self._client.messages.create(
                model=self.settings.claude_vision_model,
                max_tokens=200,
                system="Suggest concise, accurate alt text (under 125 characters) "
                "for the image, considering the surrounding page context. "
                "Describe what the image conveys, not just what it shows. "
                "Reply with only the suggested alt text, no quotes or preamble.",
                messages=[
                    {
                        "role": "user",
                        "content": [
                            {
                                "type": "image",
                                "source": {
                                    "type": "base64",
                                    "media_type": "image/png",
                                    "data": base64.b64encode(image_png).decode(),
                                },
                            },
                            {
                                "type": "text",
                                "text": f"Page context near this image: {context or 'none'}",
                            },
                        ],
                    }
                ],
            )
            self._record_usage(response.usage)
            text_block = next((b for b in response.content if b.type == "text"), None)
            return text_block.text.strip() if text_block else None
        except Exception:
            logger.exception("Alt text suggestion failed")
            return None

    async def suggest_link_text(self, link_html: str, context: str) -> str | None:
        if not self.available or not self._budget_left():
            return None
        try:
            self.calls_made += 1
            response = await self._client.messages.create(
                model=self.settings.claude_model,
                max_tokens=100,
                system="The link text below is not descriptive out of context "
                "(e.g. 'click here', 'read more'). Suggest replacement link "
                "text that makes sense read on its own, out of context, based "
                "on the surrounding page text. Reply with only the suggested "
                "text, no quotes or preamble.",
                messages=[
                    {
                        "role": "user",
                        "content": f"Link HTML: {link_html}\nSurrounding text: {context}",
                    }
                ],
            )
            self._record_usage(response.usage)
            text_block = next((b for b in response.content if b.type == "text"), None)
            return text_block.text.strip() if text_block else None
        except Exception:
            logger.exception("Link text suggestion failed")
            return None
