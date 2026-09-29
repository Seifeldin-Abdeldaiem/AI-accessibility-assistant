import { BRAND } from "@/lib/brand";
import { CurbcutMark } from "./icons";

export default function Logo({ size = 30 }: { size?: number }) {
  return (
    <span className="logo">
      <CurbcutMark size={size} />
      <span className="logo-word">{BRAND.name}</span>
    </span>
  );
}
