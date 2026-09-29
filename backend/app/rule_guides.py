"""Hand-written, plain-English guidance for the axe-core rules that show up
most often on real sites.

This is what every visitor gets, with or without an Anthropic key: who the
problem affects, what to change, and a before/after example. Claude, when a
key is supplied, writes a fix for the exact element on the scanned page and
verifies it; this library is the free baseline that makes a no-key report
useful on its own rather than a list of findings with gaps.
"""

from __future__ import annotations

import re

from .models import Guidance

AFFECTED_GROUPS = {
    "screen-reader": "Screen reader users",
    "low-vision": "People with low vision",
    "colour-blind": "Colour-blind people",
    "keyboard": "Keyboard-only users",
    "voice": "Voice control users",
    "cognitive": "People with cognitive or learning disabilities",
    "motor": "People with limited dexterity",
    "deaf": "Deaf and hard-of-hearing people",
}

_GUIDES: dict[str, dict] = {
    "image-alt": {
        "affects": ["screen-reader"],
        "summary": "This image has no text alternative, so screen readers either skip it or read out the file name. Anyone who can't see it misses whatever it was there to show.",
        "steps": [
            "Add an alt attribute describing what the image conveys in context, not what it looks like pixel by pixel.",
            "If the image is purely decorative, use an empty alt (alt=\"\") so screen readers skip it on purpose.",
        ],
        "before": '<img src="tent.jpg">',
        "after": '<img src="tent.jpg" alt="Two-person tent pitched by a lake">',
    },
    "button-name": {
        "affects": ["screen-reader", "voice"],
        "summary": "This button has no name. Screen readers announce just \"button\", and voice control users have nothing to say to press it.",
        "steps": [
            "Put visible text inside the button that says what it does.",
            "For icon-only buttons, add visually hidden text or an aria-label that matches the action.",
        ],
        "before": '<button type="submit"></button>',
        "after": '<button type="submit">Sign up</button>',
    },
    "link-name": {
        "affects": ["screen-reader", "voice"],
        "summary": "This link has no readable name, so assistive technology announces it as just \"link\" with no hint where it goes.",
        "steps": [
            "Give the link visible text describing its destination.",
            "If the link wraps only an image or icon, give that image alt text describing the destination.",
        ],
        "before": '<a href="/cart"><svg>…</svg></a>',
        "after": '<a href="/cart"><svg aria-hidden="true">…</svg>Your cart</a>',
    },
    "label": {
        "affects": ["screen-reader", "voice", "cognitive"],
        "summary": "This form field has no label. Screen readers just say \"edit text\", and placeholder text disappears as soon as someone starts typing, which trips up people with memory difficulties.",
        "steps": [
            "Add a visible <label> tied to the field with for/id.",
            "Keep the placeholder only as an example, never as the only label.",
        ],
        "before": '<input type="email" placeholder="Email">',
        "after": '<label for="email">Email address</label>\n<input type="email" id="email" autocomplete="email">',
    },
    "select-name": {
        "affects": ["screen-reader", "voice"],
        "summary": "This dropdown has no label, so people using a screen reader hear the options with no idea what they're choosing.",
        "steps": ["Add a visible <label> linked to the <select> with for/id."],
        "before": '<select name="size">…</select>',
        "after": '<label for="size">Size</label>\n<select id="size" name="size">…</select>',
    },
    "color-contrast": {
        "affects": ["low-vision", "colour-blind"],
        "summary": "This text doesn't stand out enough from its background. People with low vision, colour blindness, or just a phone in bright sunlight will struggle to read it.",
        "steps": [
            "Darken the text or lighten the background until the contrast ratio is at least 4.5:1 (3:1 for large text).",
            "Check hover, focus and disabled states too, not just the default.",
        ],
        "before": ".note { color: #aaaaaa; background: #ffffff; }",
        "after": ".note { color: #595959; background: #ffffff; } /* 7:1 */",
    },
    "html-has-lang": {
        "affects": ["screen-reader", "cognitive"],
        "summary": "The page doesn't declare its language, so screen readers guess — and may read English text with the wrong accent and pronunciation rules. Translation and reading tools rely on it too.",
        "steps": ["Add a lang attribute to the <html> element."],
        "before": "<html>",
        "after": '<html lang="en">',
    },
    "html-lang-valid": {
        "affects": ["screen-reader"],
        "summary": "The page's lang attribute isn't a real language code, so screen readers can't pick the right voice.",
        "steps": ["Use a valid BCP 47 code, such as en, en-GB, fr or ar."],
        "before": '<html lang="english">',
        "after": '<html lang="en">',
    },
    "document-title": {
        "affects": ["screen-reader", "cognitive"],
        "summary": "The page has no title. It's the first thing a screen reader announces and what people see in tabs, bookmarks and history.",
        "steps": ["Add a <title> that names the page and the site, most specific part first."],
        "before": "<head>…</head>",
        "after": "<head>\n  <title>Checkout – Example Shop</title>\n</head>",
    },
    "landmark-one-main": {
        "affects": ["screen-reader", "keyboard"],
        "summary": "There's no main region, so screen reader users can't jump straight past the navigation to the content.",
        "steps": ["Wrap the page's primary content in a single <main> element."],
        "before": '<div class="content">…</div>',
        "after": '<main class="content">…</main>',
    },
    "region": {
        "affects": ["screen-reader"],
        "summary": "Some content sits outside any landmark (header, nav, main, footer), so people navigating by landmarks can skip right past it.",
        "steps": [
            "Put all visible content inside landmark elements: <header>, <nav>, <main>, <aside> or <footer>.",
        ],
        "before": "<body>\n  <h1>Shop</h1>\n  …\n</body>",
        "after": "<body>\n  <main>\n    <h1>Shop</h1>\n    …\n  </main>\n</body>",
    },
    "page-has-heading-one": {
        "affects": ["screen-reader", "cognitive"],
        "summary": "The page has no top-level heading. Screen reader users often jump to the <h1> first to find out where they are.",
        "steps": ["Add one <h1> describing the page's main purpose."],
    },
    "heading-order": {
        "affects": ["screen-reader", "cognitive"],
        "summary": "Heading levels skip (for example h2 straight to h4), which makes the page outline confusing for people who navigate by headings.",
        "steps": [
            "Only increase heading levels one at a time.",
            "Pick heading levels for structure; change the look with CSS, not by choosing a different level.",
        ],
        "before": "<h2>Plans</h2>\n<h4>Basic</h4>",
        "after": "<h2>Plans</h2>\n<h3>Basic</h3>",
    },
    "empty-heading": {
        "affects": ["screen-reader"],
        "summary": "This heading has no text. Screen readers announce an empty heading, which is confusing and wastes a navigation stop.",
        "steps": ["Add text to the heading, or remove the heading element if it's only used for spacing."],
    },
    "list": {
        "affects": ["screen-reader"],
        "summary": "This list contains elements other than list items, so screen readers can't announce how many items it has.",
        "steps": ["Make sure <ul> and <ol> only contain <li> elements (plus <script> or <template>)."],
    },
    "listitem": {
        "affects": ["screen-reader"],
        "summary": "A list item sits outside a list, so it loses its meaning for screen reader users.",
        "steps": ["Wrap <li> elements in a <ul> or <ol>."],
    },
    "aria-hidden-focus": {
        "affects": ["screen-reader", "keyboard"],
        "summary": "Something hidden from screen readers can still receive keyboard focus, so people land on an element that announces nothing.",
        "steps": [
            "Remove aria-hidden, or make the element and everything inside it unfocusable (tabindex=\"-1\" or the inert attribute).",
        ],
    },
    "aria-required-attr": {
        "affects": ["screen-reader"],
        "summary": "An element uses an ARIA role without the attributes that role needs, so assistive technology gets incomplete information.",
        "steps": [
            "Prefer the native HTML element (a real <button>, <input type=\"checkbox\">) over an ARIA role.",
            "If you keep the role, add the attributes it requires (for example aria-checked on role=\"checkbox\").",
        ],
    },
    "aria-valid-attr-value": {
        "affects": ["screen-reader"],
        "summary": "An ARIA attribute has an invalid value, so assistive technology may ignore it or announce the wrong thing.",
        "steps": ["Fix the value (for example, aria-labelledby must point at an id that exists)."],
    },
    "aria-allowed-attr": {
        "affects": ["screen-reader"],
        "summary": "An element has an ARIA attribute that isn't allowed on it, which can confuse assistive technology.",
        "steps": ["Remove the attribute, or use an element or role that supports it."],
    },
    "duplicate-id-aria": {
        "affects": ["screen-reader"],
        "summary": "Two elements share an id that ARIA or a label points at, so the label can end up attached to the wrong thing.",
        "steps": ["Give every id on the page a unique value."],
    },
    "frame-title": {
        "affects": ["screen-reader"],
        "summary": "This embedded frame has no title, so screen reader users can't tell what it contains before entering it.",
        "steps": ["Add a title attribute describing the frame's content."],
        "before": '<iframe src="https://maps.example.com/…"></iframe>',
        "after": '<iframe src="https://maps.example.com/…" title="Map of our shop location"></iframe>',
    },
    "input-image-alt": {
        "affects": ["screen-reader", "voice"],
        "summary": "This image button has no alternative text, so it's announced without saying what it does.",
        "steps": ["Add alt text describing the action, like alt=\"Search\"."],
    },
    "svg-img-alt": {
        "affects": ["screen-reader"],
        "summary": "This SVG is marked as an image but has no text alternative.",
        "steps": ["Add a <title> inside the SVG or an aria-label, or aria-hidden=\"true\" if it's decorative."],
    },
    "role-img-alt": {
        "affects": ["screen-reader"],
        "summary": "This element is marked as an image but has no text alternative.",
        "steps": ["Add an aria-label describing it, or remove role=\"img\" if it's decorative."],
    },
    "meta-viewport": {
        "affects": ["low-vision"],
        "summary": "The page stops people from zooming in on mobile. People with low vision rely on pinch-zoom to read.",
        "steps": ["Remove user-scalable=no and any maximum-scale below 2 from the viewport meta tag."],
        "before": '<meta name="viewport" content="width=device-width, user-scalable=no">',
        "after": '<meta name="viewport" content="width=device-width, initial-scale=1">',
    },
    "link-in-text-block": {
        "affects": ["colour-blind", "low-vision"],
        "summary": "This link is only distinguished from surrounding text by colour, which colour-blind people may not be able to see.",
        "steps": ["Underline links in running text, or give them another non-colour cue."],
    },
    "nested-interactive": {
        "affects": ["screen-reader", "keyboard"],
        "summary": "An interactive element sits inside another one (like a button inside a link), which assistive technology can't announce or operate reliably.",
        "steps": ["Restructure so interactive elements sit side by side instead of inside each other."],
    },
    "scrollable-region-focusable": {
        "affects": ["keyboard"],
        "summary": "This scrolling area can't be reached with the keyboard, so keyboard users can't scroll to see what's in it.",
        "steps": ["Add tabindex=\"0\" and an accessible name to the scrolling container, or make sure it contains focusable content."],
    },
    "tabindex": {
        "affects": ["keyboard"],
        "summary": "A positive tabindex forces this element out of the natural tab order, which makes keyboard navigation jump around unpredictably.",
        "steps": ["Use tabindex=\"0\" or \"-1\" only, and fix focus order by reordering the HTML."],
    },
    "bypass": {
        "affects": ["keyboard", "screen-reader"],
        "summary": "There's no way to skip repeated navigation, so keyboard users have to tab through every menu link on every page.",
        "steps": ["Add a \"Skip to main content\" link as the first focusable element, pointing at <main>."],
        "before": "<body>\n  <nav>…</nav>",
        "after": '<body>\n  <a class="skip-link" href="#main">Skip to main content</a>\n  <nav>…</nav>\n  <main id="main">',
    },
    "image-redundant-alt": {
        "affects": ["screen-reader"],
        "summary": "The image's alt text repeats nearby text, so screen reader users hear the same thing twice.",
        "steps": ["Use alt=\"\" when the adjacent text already describes the image."],
    },
    "video-caption": {
        "affects": ["deaf"],
        "summary": "This video has no captions, so deaf and hard-of-hearing people miss everything that's said.",
        "steps": ["Add a captions track with <track kind=\"captions\">."],
    },
    "autocomplete-valid": {
        "affects": ["cognitive", "motor"],
        "summary": "This field's autocomplete value isn't valid, so browsers can't fill it in — which matters most for people who find typing slow or error-prone.",
        "steps": ["Use a standard token such as email, name, tel, street-address or postal-code."],
    },
    "target-size": {
        "affects": ["motor"],
        "summary": "This control is too small or too close to others, so people with tremors or limited dexterity keep tapping the wrong thing.",
        "steps": ["Make touch targets at least 24×24 CSS pixels, or add enough space around them."],
    },
    "label-title-only": {
        "affects": ["screen-reader", "voice", "cognitive"],
        "summary": "This field is only labelled by a tooltip, which isn't visible to most people and isn't reliably announced.",
        "steps": ["Add a visible <label>."],
    },
}

_FIX_LINE = re.compile(r"^\s*Fix (?:any|all) of the following:\s*$", re.IGNORECASE)

# For rules without a hand-written guide, axe's own category tags are a
# reasonable, non-invented signal for who's affected.
_CATEGORY_AFFECTS = {
    "cat.color": ["low-vision", "colour-blind"],
    "cat.keyboard": ["keyboard"],
    "cat.text-alternatives": ["screen-reader"],
    "cat.forms": ["screen-reader", "voice"],
    "cat.aria": ["screen-reader"],
    "cat.name-role-value": ["screen-reader", "voice"],
    "cat.structure": ["screen-reader"],
    "cat.semantics": ["screen-reader"],
    "cat.language": ["screen-reader"],
    "cat.sensory-and-visual-cues": ["low-vision"],
    "cat.tables": ["screen-reader"],
    "cat.time-and-media": ["deaf"],
}


def _affects_from_tags(tags: list[str]) -> list[str]:
    affects: list[str] = []
    for tag in tags:
        for group in _CATEGORY_AFFECTS.get(tag, []):
            if group not in affects:
                affects.append(group)
    return affects


def _steps_from_failure_summary(failure_summary: str) -> list[str]:
    """axe's failureSummary reads like "Fix any of the following:\n  Element
    has no title attribute\n  ...". The indented lines are specific,
    per-element hints, so they make a reasonable fallback checklist."""
    steps = []
    for line in failure_summary.splitlines():
        if not line.strip() or _FIX_LINE.match(line):
            continue
        text = line.strip()
        steps.append(text[0].upper() + text[1:] if text else text)
    return steps[:4]


def build_guidance(
    *,
    rule_id: str,
    description: str,
    help_text: str,
    failure_summary: str,
    tags: list[str],
) -> Guidance:
    guide = _GUIDES.get(rule_id)
    if guide:
        return Guidance(
            affects=guide["affects"],
            summary=guide["summary"],
            steps=guide["steps"],
            example_before=guide.get("before"),
            example_after=guide.get("after"),
            curated=True,
        )

    steps = _steps_from_failure_summary(failure_summary) or [help_text]
    return Guidance(
        affects=_affects_from_tags(tags),
        summary=description.rstrip(".") + ".",
        steps=steps,
        curated=False,
    )
