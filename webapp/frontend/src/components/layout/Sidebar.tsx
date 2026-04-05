import { useState } from "react";
import { NavLink, useLocation } from "react-router-dom";
import { motion, AnimatePresence } from "framer-motion";
import {
  LayoutDashboard, Database, Brain, FlaskConical, TrendingUp,
  AlertTriangle, Target, PieChart, Settings, HelpCircle,
  ChevronLeft, ChevronRight, Sparkles,
} from "lucide-react";
import { cn } from "@/lib/utils";

const routes = [
  { path: "/", icon: LayoutDashboard, label: "Overview" },
  { path: "/data", icon: Database, label: "Data Explorer" },
  { path: "/models", icon: Brain, label: "Models" },
  { path: "/experiments", icon: FlaskConical, label: "Experiments" },
  { path: "/forecasting", icon: TrendingUp, label: "Forecasting" },
  { path: "/anomalies", icon: AlertTriangle, label: "Anomalies" },
  { path: "/optimization", icon: Target, label: "Optimization" },
  { path: "/market-share", icon: PieChart, label: "Market Share" },
  { divider: true },
  { path: "/settings", icon: Settings, label: "Settings" },
  { path: "/help", icon: HelpCircle, label: "Help" },
] as const;

export function AppSidebar() {
  const [collapsed, setCollapsed] = useState(false);
  const location = useLocation();

  return (
    <motion.aside
      animate={{ width: collapsed ? 72 : 256 }}
      transition={{ duration: 0.2, ease: "easeInOut" }}
      className="relative flex flex-col border-r border-sidebar-border bg-sidebar h-screen sticky top-0 z-40 overflow-hidden"
    >
      {/* Logo */}
      <div className="flex items-center gap-3 px-4 h-16 border-b border-sidebar-border shrink-0">
        <div className="w-8 h-8 rounded-lg bg-primary/20 flex items-center justify-center shrink-0">
          <Sparkles className="w-4 h-4 text-primary" />
        </div>
        <AnimatePresence>
          {!collapsed && (
            <motion.div
              initial={{ opacity: 0 }}
              animate={{ opacity: 1 }}
              exit={{ opacity: 0 }}
              className="flex flex-col leading-tight"
            >
              <span className="text-sm font-bold tracking-wide text-sidebar-accent-foreground whitespace-nowrap">
                AURA AI
              </span>
              <span className="text-[10px] text-sidebar-foreground/70 whitespace-nowrap">
                Unified Research for HVAC Analytics
              </span>
            </motion.div>
          )}
        </AnimatePresence>
      </div>

      {/* Nav */}
      <nav className="flex-1 py-3 px-2 space-y-0.5 overflow-y-auto">
        {routes.map((route, i) => {
          if ("divider" in route) {
            return <div key={i} className="my-3 mx-2 border-t border-sidebar-border" />;
          }
          const isActive = location.pathname === route.path;
          return (
            <NavLink
              key={route.path}
              to={route.path}
              className={cn(
                "flex items-center gap-3 px-3 py-2.5 rounded-xl text-sm transition-all duration-200 group relative",
                isActive
                  ? "bg-sidebar-accent text-sidebar-primary font-medium"
                  : "text-sidebar-foreground hover:text-sidebar-accent-foreground hover:bg-sidebar-accent/50"
              )}
            >
              {isActive && (
                <motion.div
                  layoutId="sidebar-active"
                  className="absolute left-0 top-1/2 -translate-y-1/2 w-[3px] h-6 rounded-r-full bg-primary"
                  transition={{ type: "spring", stiffness: 300, damping: 30 }}
                />
              )}
              <route.icon className={cn("w-[18px] h-[18px] shrink-0", isActive && "text-primary")} />
              <AnimatePresence>
                {!collapsed && (
                  <motion.span
                    initial={{ opacity: 0 }}
                    animate={{ opacity: 1 }}
                    exit={{ opacity: 0 }}
                    className="whitespace-nowrap"
                  >
                    {route.label}
                  </motion.span>
                )}
              </AnimatePresence>
            </NavLink>
          );
        })}
      </nav>

      {/* Collapse */}
      <button
        onClick={() => setCollapsed(!collapsed)}
        className="flex items-center justify-center h-12 border-t border-sidebar-border text-sidebar-foreground hover:text-sidebar-accent-foreground transition-colors"
      >
        {collapsed ? <ChevronRight className="w-4 h-4" /> : <ChevronLeft className="w-4 h-4" />}
      </button>
    </motion.aside>
  );
}
