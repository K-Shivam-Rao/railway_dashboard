import dynamic from "next/dynamic";

export const DynamicCommandPalette = dynamic(
  () => import("@/components/layout/command-palette").then((m) => ({ default: m.CommandPalette })),
  { ssr: false }
);

export const DynamicParticleBg = dynamic(
  () => import("@/components/layout/particle-bg").then((m) => ({ default: m.ParticleBackground })),
  { ssr: false }
);

export function createLazyComponent<T>(
  importFn: () => Promise<{ default: React.ComponentType<T> }>,
  options?: { ssr?: boolean }
) {
  return dynamic(importFn, { ssr: options?.ssr ?? true });
}