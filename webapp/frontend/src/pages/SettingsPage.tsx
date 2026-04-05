import { useState } from "react";
import { motion } from "framer-motion";
import { Settings as SettingsIcon, Sun, Moon, Bug, Globe } from "lucide-react";
import { PageHeader } from "@/components/common/PageHeader";
import { Input } from "@/components/ui/input";
import { Switch } from "@/components/ui/switch";
import { Label } from "@/components/ui/label";
import { Button } from "@/components/ui/button";
import { getApiCallLog, clearApiCallLog } from "@/lib/api-client";

export default function SettingsPage() {
  const [apiUrl, setApiUrl] = useState(localStorage.getItem("api_base_url") || "http://localhost:8001");
  const [mockMode, setMockMode] = useState(localStorage.getItem("mock_mode") === "true");

  const saveApiUrl = () => localStorage.setItem("api_base_url", apiUrl);
  const toggleMock = (val: boolean) => {
    setMockMode(val);
    localStorage.setItem("mock_mode", String(val));
  };

  return (
    <div className="page-container">
      <PageHeader icon={SettingsIcon} title="Settings" description="Configure API, theme, and debug options" />

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        <motion.div initial={{ opacity: 0, y: 20 }} animate={{ opacity: 1, y: 0 }} className="glass-card p-6 space-y-5">
          <h3 className="section-title flex items-center gap-2"><Globe className="w-4 h-4 text-primary" /> API Configuration</h3>
          <div className="space-y-2">
            <Label className="text-xs text-muted-foreground">API Base URL</Label>
            <div className="flex gap-2">
              <Input value={apiUrl} onChange={e => setApiUrl(e.target.value)} className="font-mono text-xs bg-muted/50 border-0" />
              <Button variant="outline" size="sm" onClick={saveApiUrl}>Save</Button>
            </div>
          </div>
          <div className="flex items-center justify-between">
            <div>
              <Label className="text-sm">Mock Mode</Label>
              <p className="text-xs text-muted-foreground">Use placeholder data instead of real API</p>
            </div>
            <Switch checked={mockMode} onCheckedChange={toggleMock} />
          </div>
        </motion.div>

        <motion.div initial={{ opacity: 0, y: 20 }} animate={{ opacity: 1, y: 0 }} transition={{ delay: 0.1 }} className="glass-card p-6 space-y-5">
          <h3 className="section-title flex items-center gap-2"><Bug className="w-4 h-4 text-primary" /> Debug Panel</h3>
          <div className="bg-muted/50 rounded-xl p-4 space-y-2 max-h-64 overflow-auto">
            {getApiCallLog().length === 0 ? (
              <p className="text-xs text-muted-foreground text-center py-4">No API calls recorded yet. Navigate the app to see calls here.</p>
            ) : (
              getApiCallLog().slice(-10).reverse().map((call, i) => (
                <div key={i} className="flex items-center justify-between text-xs py-1 border-b border-border/30">
                  <span className="font-mono">{call.method} {new URL(call.url).pathname}</span>
                  <div className="flex items-center gap-3">
                    <span className={call.status >= 200 && call.status < 300 ? "text-accent" : "text-destructive"}>{call.status || "ERR"}</span>
                    <span className="text-muted-foreground">{call.duration.toFixed(0)}ms</span>
                  </div>
                </div>
              ))
            )}
          </div>
          <Button variant="outline" size="sm" onClick={clearApiCallLog}>Clear Logs</Button>
        </motion.div>
      </div>
    </div>
  );
}
