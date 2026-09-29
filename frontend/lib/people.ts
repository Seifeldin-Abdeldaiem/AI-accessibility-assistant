import type { ViolationGroup } from "./types";

// Keys match backend/app/rule_guides.py AFFECTED_GROUPS.
export const PEOPLE: Record<string, { label: string; short: string }> = {
  "screen-reader": { label: "Screen reader users", short: "Screen readers" },
  "low-vision": { label: "People with low vision", short: "Low vision" },
  "colour-blind": { label: "Colour-blind people", short: "Colour blindness" },
  keyboard: { label: "Keyboard-only users", short: "Keyboard only" },
  voice: { label: "Voice control users", short: "Voice control" },
  cognitive: { label: "People with cognitive or learning disabilities", short: "Cognitive" },
  motor: { label: "People with limited dexterity", short: "Dexterity" },
  deaf: { label: "Deaf and hard-of-hearing people", short: "Deaf / HoH" },
};

export function peopleAffected(groups: ViolationGroup[]): { key: string; count: number }[] {
  const counts = new Map<string, number>();
  for (const g of groups) {
    for (const key of g.guidance?.affects ?? []) {
      counts.set(key, (counts.get(key) ?? 0) + 1);
    }
  }
  return [...counts.entries()]
    .map(([key, count]) => ({ key, count }))
    .sort((a, b) => b.count - a.count);
}
