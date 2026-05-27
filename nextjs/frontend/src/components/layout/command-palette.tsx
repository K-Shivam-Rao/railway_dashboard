"use client";

import { useEffect } from "react";
import { useRouter } from "next/navigation";
import { motion, AnimatePresence } from "framer-motion";
import { useUIStore } from "@/stores/ui-store";
import { NAV_ITEMS } from "@/lib/constants";
import { Search, Command } from "lucide-react";

const iconMap: Record<string, string> = {
  Activity: "⌘1", TrendingUp: "⌘2", AlertTriangle: "⌘3",
  Network: "⌘4", DollarSign: "⌘5", Users: "⌘6",
  BarChart3: "⌘7", PieChart: "⌘8", Brain: "⌘9",
  Layers: "⌘0", Building2: "⌘-",
};

export function CommandPalette() {
  const router = useRouter();
  const { commandPaletteOpen, setCommandPaletteOpen } = useUIStore();

  useEffect(() => {
    if (!commandPaletteOpen) return;
    function handleKey(e: KeyboardEvent) {
      if (e.key === "Escape") {
        setCommandPaletteOpen(false);
      }
    }
    window.addEventListener("keydown", handleKey);
    return () => window.removeEventListener("keydown", handleKey);
  }, [commandPaletteOpen, setCommandPaletteOpen]);

  return (
    <AnimatePresence>
      {commandPaletteOpen && (
        <motion.div
          initial={{ opacity: 0 }}
          animate={{ opacity: 1 }}
          exit={{ opacity: 0 }}
          className="fixed inset-0 z-50 flex items-start justify-center pt-[15vh] bg-black/60 backdrop-blur-sm"
          onClick={() => setCommandPaletteOpen(false)}
        >
          <motion.div
            initial={{ scale: 0.95, opacity: 0 }}
            animate={{ scale: 1, opacity: 1 }}
            exit={{ scale: 0.95, opacity: 0 }}
            transition={{ duration: 0.15 }}
            onClick={(e) => e.stopPropagation()}
            className="w-full max-w-lg rounded-xl border border-border-default bg-bg-surface shadow-2xl overflow-hidden"
          >
            <div className="flex items-center gap-3 px-4 py-3 border-b border-border-default">
              <Search className="w-4 h-4 text-text-muted" />
              <input
                autoFocus
                placeholder="Search views, or type a command..."
                className="flex-1 bg-transparent text-sm text-text-primary outline-none placeholder:text-text-muted"
              />
              <kbd className="hidden sm:inline-flex items-center gap-1 px-1.5 py-0.5 text-xs text-text-muted bg-bg-elevated rounded">
                <Command className="w-3 h-3" />K
              </kbd>
            </div>

            <div className="py-2 max-h-80 overflow-y-auto">
              <p className="px-4 py-1.5 text-xs text-text-muted font-medium uppercase tracking-wider">
                Views
              </p>
              {NAV_ITEMS.map((item) => (
                <button
                  key={item.href}
                  onClick={() => {
                    router.push(item.href);
                    setCommandPaletteOpen(false);
                  }}
                  className="w-full flex items-center gap-3 px-4 py-2.5 text-sm text-text-secondary hover:text-text-primary hover:bg-bg-elevated transition-colors text-left"
                >
                  <span>{item.label}</span>
                  <span className="ml-auto text-xs text-text-muted">{iconMap[item.icon] || ""}</span>
                </button>
              ))}

              <p className="px-4 py-1.5 text-xs text-text-muted font-medium uppercase tracking-wider mt-2">
                Actions
              </p>
              <button
                onClick={() => setCommandPaletteOpen(false)}
                className="w-full flex items-center gap-3 px-4 py-2.5 text-sm text-text-secondary hover:text-text-primary hover:bg-bg-elevated transition-colors text-left"
              >
                <span>Generate Report</span>
              </button>
              <button
                onClick={() => setCommandPaletteOpen(false)}
                className="w-full flex items-center gap-3 px-4 py-2.5 text-sm text-text-secondary hover:text-text-primary hover:bg-bg-elevated transition-colors text-left"
              >
                <span>Export Data</span>
                <span className="ml-auto text-xs text-text-muted">⌘P</span>
              </button>
            </div>

            <div className="px-4 py-2 border-t border-border-default text-xs text-text-muted">
              Press <kbd className="px-1 py-0.5 bg-bg-elevated rounded text-text-secondary">Esc</kbd> to close
            </div>
          </motion.div>
        </motion.div>
      )}
    </AnimatePresence>
  );
}