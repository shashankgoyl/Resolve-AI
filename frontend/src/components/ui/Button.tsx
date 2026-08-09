import { ButtonHTMLAttributes, forwardRef } from "react";
import { cn } from "@/lib/utils";

type Variant = "primary" | "secondary" | "ghost" | "danger" | "outline";
type Size = "sm" | "md";

const variants: Record<Variant, string> = {
  primary: "bg-signal-teal text-ink font-medium hover:bg-signal-teal/90 shadow-[0_0_0_1px_rgba(79,209,197,0.4)]",
  secondary: "bg-signal-indigo/15 text-signal-indigo border border-signal-indigo/30 hover:bg-signal-indigo/25",
  outline: "bg-transparent border border-ink-border text-text-primary hover:bg-white/5",
  ghost: "bg-transparent text-text-muted hover:text-text-primary hover:bg-white/5",
  danger: "bg-signal-coral/15 text-signal-coral border border-signal-coral/30 hover:bg-signal-coral/25",
};

const sizes: Record<Size, string> = {
  sm: "text-xs px-2.5 py-1.5 gap-1.5",
  md: "text-sm px-3.5 py-2 gap-2",
};

export interface ButtonProps extends ButtonHTMLAttributes<HTMLButtonElement> {
  variant?: Variant;
  size?: Size;
}

export const Button = forwardRef<HTMLButtonElement, ButtonProps>(
  ({ className, variant = "outline", size = "md", ...props }, ref) => (
    <button
      ref={ref}
      className={cn(
        "inline-flex items-center justify-center rounded-lg font-body transition-colors duration-150 disabled:opacity-40 disabled:pointer-events-none whitespace-nowrap",
        variants[variant],
        sizes[size],
        className
      )}
      {...props}
    />
  )
);
Button.displayName = "Button";
