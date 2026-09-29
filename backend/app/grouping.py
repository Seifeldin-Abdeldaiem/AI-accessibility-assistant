from __future__ import annotations

from .models import ViolationGroup, ViolationNode
from .rule_guides import build_guidance
from .scanner import RawViolation

# WCAG success-criterion tags look like "wcag111", "wcag412"; axe also
# includes non-WCAG tags (best-practice, cat.*, etc). Surface only the
# WCAG ones in the report — that's what a user needs to cite.
def _wcag_tags(tags: list[str]) -> list[str]:
    return [t for t in tags if t.startswith("wcag") and t[4:].isdigit()]


def build_violation_groups(violations: list[RawViolation]) -> list[ViolationGroup]:
    """One group per axe rule. Within a rule, collapse nodes that share the
    same HTML down to a single representative — a product listing with 40
    images missing alt text is one fix applied in 40 places, not 40 distinct
    problems to read about."""
    groups: list[ViolationGroup] = []

    for v in violations:
        seen_html: set[str] = set()
        deduped_nodes: list[ViolationNode] = []
        for n in v.nodes:
            key = n.html.strip()
            if key in seen_html:
                continue
            seen_html.add(key)
            deduped_nodes.append(
                ViolationNode(
                    target=n.target,
                    html=n.html,
                    failure_summary=n.failure_summary,
                    bounding_box=n.bounding_box,
                )
            )

        groups.append(
            ViolationGroup(
                rule_id=v.rule_id,
                impact=v.impact,
                description=v.description,
                help_text=v.help_text,
                help_url=v.help_url,
                wcag_tags=_wcag_tags(v.tags),
                nodes=deduped_nodes,
                total_node_count=v.total_node_count,
                guidance=build_guidance(
                    rule_id=v.rule_id,
                    description=v.description,
                    help_text=v.help_text,
                    failure_summary=deduped_nodes[0].failure_summary if deduped_nodes else "",
                    tags=v.tags,
                ),
            )
        )

    impact_order = {"critical": 0, "serious": 1, "moderate": 2, "minor": 3}
    groups.sort(key=lambda g: (impact_order.get(g.impact, 4), -g.total_node_count))
    return groups
