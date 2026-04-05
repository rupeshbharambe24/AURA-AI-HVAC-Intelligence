import { motion } from "framer-motion";
import { HelpCircle, BookOpen, Code, ExternalLink } from "lucide-react";
import { PageHeader } from "@/components/common/PageHeader";
import { Button } from "@/components/ui/button";

const guides = [
  { title: "Getting Started", desc: "Learn how to navigate the platform and run your first prediction." },
  { title: "Model Cards", desc: "Understanding model transparency, metrics, and limitations." },
  { title: "Experiment Tracking", desc: "Compare runs, view artifacts, and manage model versions." },
  { title: "Promotion Optimization", desc: "Set constraints, run async jobs, and interpret results." },
  { title: "API Integration", desc: "Connect your backend to the Nexus AI API endpoints." },
];

export default function Help() {
  return (
    <div className="page-container">
      <PageHeader icon={HelpCircle} title="Help & Documentation" description="Guides, API explorer, and support resources" />

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        <div className="space-y-4">
          <h2 className="section-title flex items-center gap-2"><BookOpen className="w-4 h-4 text-primary" /> Usage Guides</h2>
          {guides.map((g, i) => (
            <motion.div
              key={g.title}
              initial={{ opacity: 0, x: -10 }}
              animate={{ opacity: 1, x: 0 }}
              transition={{ delay: i * 0.05 }}
              className="glass-card-hover p-5 cursor-pointer"
            >
              <h3 className="text-sm font-semibold">{g.title}</h3>
              <p className="text-xs text-muted-foreground mt-1">{g.desc}</p>
            </motion.div>
          ))}
        </div>

        <div className="space-y-4">
          <h2 className="section-title flex items-center gap-2"><Code className="w-4 h-4 text-primary" /> API Explorer</h2>
          <motion.div initial={{ opacity: 0 }} animate={{ opacity: 1 }} transition={{ delay: 0.2 }} className="glass-card p-6 space-y-4">
            <p className="text-sm text-muted-foreground">Access the interactive API documentation to explore all available endpoints.</p>
            <div className="flex gap-3">
              <Button variant="outline" className="gap-2">
                <ExternalLink className="w-4 h-4" /> Swagger UI (/docs)
              </Button>
              <Button variant="outline" className="gap-2">
                <ExternalLink className="w-4 h-4" /> ReDoc (/redoc)
              </Button>
            </div>
          </motion.div>

          <motion.div initial={{ opacity: 0 }} animate={{ opacity: 1 }} transition={{ delay: 0.3 }} className="glass-card p-6 space-y-3">
            <h3 className="text-sm font-semibold">curl Example</h3>
            <div className="bg-muted/50 rounded-xl p-4 font-mono text-xs overflow-x-auto">
              <pre className="text-muted-foreground">{`curl -X POST http://localhost:8001/api/v1/forecast/predict \\
  -H "Content-Type: application/json" \\
  -d '{"product_id": "SKU001", "horizon_months": 6}'`}</pre>
            </div>
          </motion.div>
        </div>
      </div>
    </div>
  );
}
