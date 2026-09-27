from __future__ import annotations

import logging

from playwright.async_api import Page

from .models import ViolationGroup

logger = logging.getLogger(__name__)

# Runs entirely in the browser so the check-and-revert is atomic from
# Python's point of view: find the flagged element, snapshot its parent's
# current markup, swap in the proposed fix, re-run axe scoped to that
# parent (fast — not a full-page re-run), then always restore the parent's
# original markup so later verifications see the page as the scan saw it.
_VERIFY_JS = """
async ({ selector, newHtml, ruleId }) => {
    const el = document.querySelector(selector);
    if (!el) return { error: 'not_found' };
    const parent = el.parentElement;
    if (!parent) return { error: 'no_parent' };

    const originalParentHtml = parent.innerHTML;

    try {
        const before = await axe.run(parent, { resultTypes: ['violations'] });
        const beforeOtherIds = new Set(
            before.violations.filter(v => v.id !== ruleId).map(v => v.id)
        );

        el.outerHTML = newHtml;

        const after = await axe.run(parent, { resultTypes: ['violations'] });
        const afterViolation = after.violations.find(v => v.id === ruleId);
        const afterOtherIds = new Set(
            after.violations.filter(v => v.id !== ruleId).map(v => v.id)
        );

        const newRuleIds = [...afterOtherIds].filter(id => !beforeOtherIds.has(id));

        return {
            error: null,
            resolved: !afterViolation,
            newRuleIds,
        };
    } finally {
        parent.innerHTML = originalParentHtml;
    }
}
"""


async def verify_fix(page: Page, group: ViolationGroup) -> None:
    if not group.fix or not group.nodes:
        return

    selector = group.nodes[0].target
    if not selector:
        group.fix_verified = None
        group.fix_verification_note = "Could not verify: no stable selector captured for this element."
        return

    try:
        result = await page.evaluate(
            _VERIFY_JS,
            {"selector": selector, "newHtml": group.fix.new_html, "ruleId": group.rule_id},
        )
    except Exception as exc:  # noqa: BLE001
        logger.warning("Fix verification crashed for rule %s: %s", group.rule_id, exc)
        group.fix_verified = None
        group.fix_verification_note = f"Could not verify: {exc}"
        return

    if result.get("error") == "not_found":
        group.fix_verified = None
        group.fix_verification_note = (
            "Could not verify: element was not found in the DOM when re-checked "
            "(the page may be dynamic)."
        )
        return
    if result.get("error") == "no_parent":
        group.fix_verified = None
        group.fix_verification_note = "Could not verify: element has no parent to scope the re-check to."
        return

    resolved = bool(result.get("resolved"))
    new_rule_ids = result.get("newRuleIds") or []

    if resolved and not new_rule_ids:
        group.fix_verified = True
        group.fix_verification_note = "Applied in a real browser and re-checked: issue gone, nothing new introduced."
    elif resolved and new_rule_ids:
        group.fix_verified = False
        group.fix_verification_note = (
            f"This issue was resolved, but the fix introduced new issue(s): {', '.join(new_rule_ids)}. "
            "Review before applying."
        )
    else:
        group.fix_verified = False
        group.fix_verification_note = (
            "Applied fix did not clear the issue when re-checked. Treat this as a suggestion, not a verified fix."
        )
