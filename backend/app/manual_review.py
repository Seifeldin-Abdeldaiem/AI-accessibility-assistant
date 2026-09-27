from __future__ import annotations

import logging

from playwright.async_api import Page

from .claude_client import ClaudeClient
from .models import ManualReviewItem

logger = logging.getLogger(__name__)

# axe-core can only judge whether alt text exists, not whether it's useful.
# This runs in the browser to flag likely low-quality candidates for a
# human (and Claude) to look at: it's a heuristic, not a WCAG rule.
_FIND_CANDIDATES_JS = """
() => {
    function selectorFor(el) {
        const parts = [];
        let node = el;
        while (node && node.nodeType === 1 && node !== document.body) {
            let part = node.tagName.toLowerCase();
            const parent = node.parentElement;
            if (parent) {
                const siblings = Array.from(parent.children).filter(
                    c => c.tagName === node.tagName
                );
                if (siblings.length > 1) {
                    part += `:nth-of-type(${siblings.indexOf(node) + 1})`;
                }
            }
            parts.unshift(part);
            node = node.parentElement;
        }
        return 'body > ' + parts.join(' > ');
    }

    const filenamePattern = /\\.(jpe?g|png|gif|svg|webp|bmp|avif)([?#].*)?$/i;
    const genericAltPattern = /^(img|image|photo|pic(ture)?|dsc|screenshot|untitled|asset|graphic)[-_ ]?\\d*$/i;
    const genericLinkPhrases = new Set([
        'click here', 'here', 'read more', 'more', 'learn more', 'link',
        'this link', 'details', 'continue', 'go', 'click', 'more info',
        'find out more',
    ]);

    const altCandidates = [];
    for (const img of document.querySelectorAll('img[alt]')) {
        const alt = img.getAttribute('alt').trim();
        if (!alt) continue; // empty alt is valid for decorative images
        const src = img.getAttribute('src') || '';
        const srcFile = src.split('/').pop() || '';
        const looksLikeFilename = filenamePattern.test(alt) || (srcFile && alt === srcFile);
        const looksGeneric = genericAltPattern.test(alt);
        const tooShortForSize = alt.length <= 3 && (img.naturalWidth > 60 || img.width > 60);
        if (looksLikeFilename || looksGeneric || tooShortForSize) {
            altCandidates.push({
                selector: selectorFor(img),
                html: img.outerHTML,
                alt,
                context: (img.closest('figure, article, section, li, p')?.textContent || '')
                    .trim().slice(0, 300),
            });
        }
    }

    const linkCandidates = [];
    for (const el of document.querySelectorAll('a[href], button')) {
        const text = (el.textContent || '').trim().toLowerCase();
        if (genericLinkPhrases.has(text)) {
            const container = el.closest('li, p, article, section') || el.parentElement;
            linkCandidates.push({
                selector: selectorFor(el),
                html: el.outerHTML,
                text,
                context: (container?.textContent || '').trim().slice(0, 300),
            });
        }
    }

    return { altCandidates, linkCandidates };
}
"""

MAX_ALT_SUGGESTIONS = 5
MAX_LINK_SUGGESTIONS = 8


async def find_manual_review_items(
    page: Page, claude: ClaudeClient
) -> list[ManualReviewItem]:
    try:
        candidates = await page.evaluate(_FIND_CANDIDATES_JS)
    except Exception:
        logger.exception("Manual review candidate scan failed")
        return []

    items: list[ManualReviewItem] = []

    for c in candidates.get("altCandidates", [])[:MAX_ALT_SUGGESTIONS]:
        suggestion = None
        try:
            locator = page.locator(c["selector"]).first
            screenshot = await locator.screenshot(timeout=3000)
            suggestion = await claude.suggest_alt_text(screenshot, c["context"])
        except Exception:
            logger.info("Could not screenshot/suggest alt text for %s", c["selector"])
        items.append(
            ManualReviewItem(
                kind="alt_text",
                selector=c["selector"],
                html=c["html"],
                reason=f'The alt text ("{c["alt"]}") looks like a filename or placeholder rather '
                "than a description of what the image conveys.",
                suggestion=suggestion,
            )
        )

    for c in candidates.get("linkCandidates", [])[:MAX_LINK_SUGGESTIONS]:
        suggestion = await claude.suggest_link_text(c["html"], c["context"])
        items.append(
            ManualReviewItem(
                kind="link_text",
                selector=c["selector"],
                html=c["html"],
                reason=f'The link text ("{c["text"]}") does not make sense out of context — screen '
                "reader users often navigate by jumping between links alone.",
                suggestion=suggestion,
            )
        )

    return items
