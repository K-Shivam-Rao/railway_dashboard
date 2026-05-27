"use client";

import { useState } from "react";
import { motion, AnimatePresence } from "framer-motion";
import { usePathname } from "next/navigation";
import { Sidebar } from "@/components/layout/sidebar";
import { Header } from "@/components/layout/header";
import { DynamicCommandPalette, DynamicParticleBg } from "@/lib/dynamic-imports";
import { ErrorBoundary } from "@/components/dashboard/error-boundary";
import { useKeyboard } from "@/hooks/use-keyboard";
import { useMediaQuery } from "@/hooks/use-media-query";
import { useUIStore } from "@/stores/ui-store";
import { cn } from "@/lib/utils";
import { Menu } from "lucide-react";

export default function DashboardLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  const pathname = usePathname();
  const isMobile = useMediaQuery("(max-width: 768px)");
  const [mobileSidebarOpen, setMobileSidebarOpen] = useState(false);
  const { sidebarCollapsed } = useUIStore();

  useKeyboard();

  const sidebarVisible = isMobile ? mobileSidebarOpen : !sidebarCollapsed;

  return (
    <div className="flex h-screen relative" role="application">
      <DynamicParticleBg />

      {isMobile && mobileSidebarOpen && (
        <div
          className="fixed inset-0 bg-black/50 z-20"
          onClick={() => setMobileSidebarOpen(false)}
        />
      )}

      <div
        className={cn(
          "flex-shrink-0 z-30 transition-all duration-300",
          isMobile
            ? mobileSidebarOpen
              ? "translate-x-0 fixed"
              : "-translate-x-full fixed"
            : "relative"
        )}
      >
        <Sidebar />
      </div>

      <div className="flex-1 flex flex-col relative z-10 min-w-0">
        {isMobile && (
          <button
            onClick={() => setMobileSidebarOpen((v) => !v)}
            className="fixed top-3 left-3 z-40 p-2 rounded-lg bg-bg-surface border border-border-default text-text-secondary hover:text-text-primary"
            aria-label="Toggle sidebar"
          >
            <Menu className="w-5 h-5" />
          </button>
        )}
        <Header />
        <main className="flex-1 overflow-auto p-4 lg:p-6 bg-transparent" role="main">
          <ErrorBoundary>
            <AnimatePresence mode="wait">
              <motion.div
                key={pathname}
                initial={{ opacity: 0, y: 12 }}
                animate={{ opacity: 1, y: 0 }}
                exit={{ opacity: 0, y: -12 }}
                transition={{ duration: 0.2, ease: [0.16, 1, 0.3, 1] }}
              >
                {children}
              </motion.div>
            </AnimatePresence>
          </ErrorBoundary>
        </main>
      </div>
      <DynamicCommandPalette />
    </div>
  );
}