"use client";

import { motion } from "framer-motion";
import Link from "next/link";
import { ArrowLeft, Train } from "lucide-react";

export default function NotFound() {
  return (
    <div className="min-h-screen flex flex-col items-center justify-center bg-bg-base px-6">
      <motion.div
        initial={{ scale: 0, rotate: -180 }}
        animate={{ scale: 1, rotate: 0 }}
        transition={{ type: "spring", stiffness: 200, damping: 15 }}
        className="mb-8"
      >
        <div className="w-24 h-24 rounded-2xl bg-primary/20 flex items-center justify-center">
          <Train className="w-12 h-12 text-primary" />
        </div>
      </motion.div>

      <motion.h1
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ delay: 0.2 }}
        className="text-6xl font-bold text-text-primary mb-2"
      >
        404
      </motion.h1>

      <motion.p
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ delay: 0.3 }}
        className="text-text-secondary text-lg mb-2"
      >
        This platform has no doors
      </motion.p>

      <motion.p
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ delay: 0.4 }}
        className="text-text-muted text-sm mb-8"
      >
        The page you&apos;re looking for doesn&apos;t exist or has been moved.
      </motion.p>

      <motion.div
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ delay: 0.5 }}
      >
        <Link
          href="/ops"
          className="flex items-center gap-2 px-6 py-3 bg-primary text-black font-medium rounded-lg hover:bg-primary-light transition-colors"
        >
          <ArrowLeft className="w-4 h-4" />
          Back to Operations
        </Link>
      </motion.div>
    </div>
  );
}