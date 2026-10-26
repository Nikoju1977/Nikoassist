import { cx } from "../util";

/** NikoAssist's own identity mark, separate from the AI assistant's avatar. */
export function BrandMark({ size = 72, className }: { size?: number; className?: string }) {
  return <img src="/icon.svg" alt="NikoAssist" width={size} height={size} draggable={false} className={cx("block shrink-0 select-none", className)} style={{ width: size, height: size }} />;
}
