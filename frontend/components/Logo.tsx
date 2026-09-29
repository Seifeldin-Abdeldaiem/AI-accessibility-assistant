import { BRAND } from "@/lib/brand";
import { BrandMark } from "./icons";

export default function Logo({ size = 30 }: { size?: number }) {
  return (
    <span className="logo">
      <BrandMark size={size} />
      <span className="logo-word">{BRAND.name}</span>
    </span>
  );
}
