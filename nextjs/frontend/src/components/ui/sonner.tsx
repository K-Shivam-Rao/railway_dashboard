"use client";

import { Toaster as Sonner, ToasterProps } from "sonner";

const Toaster = ({ ...props }: ToasterProps) => {
  return (
    <Sonner
      theme="dark"
      className="toaster group"
      style={
        {
          "--normal-bg": "var(--bg-surface)",
          "--normal-text": "var(--text-primary)",
          "--normal-border": "var(--border-default)",
        } as React.CSSProperties
      }
      {...props}
    />
  );
};

export { Toaster };