import { useState } from "react";
import { Outlet, useNavigate } from "react-router-dom";
import { KeyRound, ArrowRight, X } from "lucide-react";

import Navbar from "./Navbar";
import CareerSidebar from "./CareerSidebar";
import CareerInsights from "./CareerInsights";
import "../CSS/WorkspaceLayout.css";

export default function WorkspaceLayout() {
  const navigate = useNavigate();
  const [showSetupBanner, setShowSetupBanner] = useState(true);

  return (
    <div className="workspace-layout">
      <Navbar />

      <div className="workspace-body">
        <CareerInsights />

        <main className="workspace-main">
          {showSetupBanner && (
            <div className="mx-auto max-w-4xl px-1 py-2 ai-setup-banner">
              <div className="ai-setup-banner-icon">
                <KeyRound size={18} />
              </div>

              <div className="ai-setup-banner-content">
                <span>Add your API key and pick a model to Start.</span>
              </div>

              <button
                type="button"
                className="ai-setup-banner-button"
                onClick={() => navigate("/settings")}
              >
                <span>Set up AI</span>
                <ArrowRight size={17} />
              </button>

              <button
                type="button"
                className="ai-setup-banner-close"
                aria-label="Close"
                onClick={() => setShowSetupBanner(false)}
              >
                <X size={18} />
              </button>
            </div>
          )}

          <div className="workspace-content">
            <Outlet />
          </div>
        </main>

        <CareerSidebar />
      </div>
    </div>
  );
}
