"use client";

import { motion } from "framer-motion";
import { GlassPanel } from "@/components/dashboard/glass-panel";
import { Building2, MapPin, Users, Train, Target } from "lucide-react";

const team = [
  { name: "Dr. Anna Weber", role: "CEO & Founder", dept: "Executive", initials: "AW" },
  { name: "Klaus Mueller", role: "CTO", dept: "Engineering", initials: "KM" },
  { name: "Sarah Chen", role: "CPO", dept: "Product", initials: "SC" },
  { name: "Markus Schmidt", role: "Head of Engineering", dept: "Engineering", initials: "MS" },
  { name: "Lisa Bauer", role: "Head of Data Science", dept: "Data", initials: "LB" },
  { name: "Thomas Fischer", role: "Head of Operations", dept: "Operations", initials: "TF" },
  { name: "Julia Hoffmann", role: "Head of Design", dept: "Product", initials: "JH" },
  { name: "Peter Wagner", role: "Head of Sales", dept: "Sales", initials: "PW" },
  { name: "Nina Becker", role: "Head of Security", dept: "Engineering", initials: "NB" },
];

export default function CompanyPage() {
  return (
    <div className="space-y-6">
      <GlassPanel icon={Building2} title="About SicherGleis">
        <div className="grid grid-cols-2 md:grid-cols-4 gap-6 mb-4">
          {[
            { label: "Founded", value: "2020", icon: MapPin },
            { label: "HQ", value: "Berlin, DE", icon: MapPin },
            { label: "Employees", value: "85", icon: Users },
            { label: "Stations", value: "50", icon: Train },
          ].map((item) => {
            const Icon = item.icon;
            return (
              <div key={item.label} className="text-center">
                <Icon className="w-5 h-5 text-primary mx-auto mb-2" />
                <p className="text-2xl font-bold text-text-primary">{item.value}</p>
                <p className="text-xs text-text-muted">{item.label}</p>
              </div>
            );
          })}
        </div>
        <p className="text-text-secondary text-sm leading-relaxed">
          SicherGleis provides AI-powered Platform Screen Door analytics and predictive
          maintenance solutions for modern railway infrastructure. Our platform monitors
          over 50 stations across Germany, Austria, and Switzerland, processing millions of
          sensor data points daily to ensure passenger safety and operational efficiency.
        </p>
      </GlassPanel>

      <GlassPanel icon={Target} title="Our Mission">
        <p className="text-text-secondary text-sm leading-relaxed">
          Making railway infrastructure safer, smarter, and more reliable through
          real-time intelligence and predictive analytics. We believe every station
          deserves zero-incident operations.
        </p>
      </GlassPanel>

      <GlassPanel icon={Users} title="Leadership Team">
        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-4">
          {team.map((member, i) => (
            <motion.div
              key={member.name}
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ delay: i * 0.05 }}
              className="flex items-center gap-4 p-4 rounded-lg bg-bg-elevated/50 hover:bg-bg-elevated transition-colors"
            >
              <div className="w-12 h-12 rounded-full bg-primary/20 flex items-center justify-center shrink-0">
                <span className="text-sm font-bold text-primary">{member.initials}</span>
              </div>
              <div className="min-w-0">
                <p className="text-sm font-medium text-text-primary truncate">{member.name}</p>
                <p className="text-xs text-text-muted">{member.role}</p>
              </div>
            </motion.div>
          ))}
        </div>
      </GlassPanel>
    </div>
  );
}