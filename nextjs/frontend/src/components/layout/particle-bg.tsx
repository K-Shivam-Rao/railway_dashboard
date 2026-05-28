"use client";

import { useEffect, useRef } from "react";
import { useMediaQuery } from "@/hooks/use-media-query";

export function ParticleBackground() {
  const canvasRef = useRef<HTMLCanvasElement>(null);
  const prefersReduced = useMediaQuery("(prefers-reduced-motion: reduce)");

  useEffect(() => {
    if (prefersReduced) return;

    const canvas = canvasRef.current as HTMLCanvasElement;

    const ctx = canvas.getContext("2d") as CanvasRenderingContext2D;
    let animId: number;
    let w = window.innerWidth;
    let h = window.innerHeight;

    canvas.width = w;
    canvas.height = h;

    const particleCount = Math.min(60, Math.floor((w * h) / 30000));
    const particles: { x: number; y: number; vx: number; vy: number; r: number; alpha: number }[] = [];

    for (let i = 0; i < particleCount; i++) {
      particles.push({
        x: Math.random() * w,
        y: Math.random() * h,
        vx: (Math.random() - 0.5) * 0.3,
        vy: (Math.random() - 0.5) * 0.3,
        r: Math.random() * 2 + 0.5,
        alpha: Math.random() * 0.06 + 0.02,
      });
    }

    function draw() {
      ctx.clearRect(0, 0, w, h);

      for (const p of particles) {
        p.x += p.vx;
        p.y += p.vy;

        if (p.x < 0) p.x = w;
        if (p.x > w) p.x = 0;
        if (p.y < 0) p.y = h;
        if (p.y > h) p.y = 0;

        ctx.beginPath();
        ctx.arc(p.x, p.y, p.r, 0, Math.PI * 2);
        ctx.fillStyle = `rgba(245, 158, 11, ${p.alpha})`;
        ctx.fill();
      }

      animId = requestAnimationFrame(draw);
    }

    draw();

    function resize() {
      w = window.innerWidth;
      h = window.innerHeight;
      canvas.width = w;
      canvas.height = h;
    }

    window.addEventListener("resize", resize);
    return () => {
      cancelAnimationFrame(animId);
      window.removeEventListener("resize", resize);
    };
  }, [prefersReduced]);

  if (prefersReduced) return null;

  return (
    <canvas
      ref={canvasRef}
      className="fixed inset-0 pointer-events-none z-0"
      aria-hidden="true"
    />
  );
}