const SC_NAMES: Record<string, string> = {
  "1.1.1": "Non-text Content",
  "1.2.2": "Captions",
  "1.3.1": "Info and Relationships",
  "1.3.5": "Identify Input Purpose",
  "1.4.1": "Use of Color",
  "1.4.3": "Contrast (Minimum)",
  "1.4.4": "Resize Text",
  "1.4.11": "Non-text Contrast",
  "1.4.12": "Text Spacing",
  "2.1.1": "Keyboard",
  "2.4.1": "Bypass Blocks",
  "2.4.2": "Page Titled",
  "2.4.3": "Focus Order",
  "2.4.4": "Link Purpose",
  "2.4.6": "Headings and Labels",
  "2.4.7": "Focus Visible",
  "2.5.3": "Label in Name",
  "2.5.8": "Target Size",
  "3.1.1": "Language of Page",
  "3.1.2": "Language of Parts",
  "3.3.2": "Labels or Instructions",
  "4.1.1": "Parsing",
  "4.1.2": "Name, Role, Value",
};

/** axe encodes criteria as "wcag1410" -> "1.4.10". */
export function wcagNumber(tag: string): string | null {
  const digits = tag.replace(/^wcag/, "");
  if (!/^\d{3,}$/.test(digits)) return null;
  return `${digits[0]}.${digits[1]}.${digits.slice(2)}`;
}

export function wcagLabel(tags: string[]): string {
  const numbers = tags.map(wcagNumber).filter((n): n is string => Boolean(n));
  if (numbers.length === 0) return "Best practice";
  const first = numbers[0];
  const name = SC_NAMES[first];
  const rest = numbers.length > 1 ? ` +${numbers.length - 1}` : "";
  return `WCAG ${first}${name ? ` ${name}` : ""}${rest}`;
}
