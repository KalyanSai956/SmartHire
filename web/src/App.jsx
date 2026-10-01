import { lazy, Suspense } from "react";
import { Route, Routes } from "react-router-dom";

import ProtectedRoute from "./components/ProtectedRoute";
import ProfileRequired from "./components/ProfileRequired";
import WorkspaceLayout from "./components/WorkspaceLayout";
import Job from "./pages/Jobs";
import AISettings from "./pages/AISettings";
import Resources from "./pages/Resources";
import InterviewPrep from "./pages/InterviewPrep";

const Landing = lazy(() => import("./pages/Landing"));
const Onboarding = lazy(() => import("./pages/Onboarding"));
const Dashboard = lazy(() => import("./pages/Dashboard"));
const Analyze = lazy(() => import("./pages/Analyze"));
const History = lazy(() => import("./pages/History"));
const Analysis = lazy(() => import("./pages/Analysis"));

function Protected({ children }) {
  return <ProtectedRoute>{children}</ProtectedRoute>;
}

function PageLoader() {
  return (
    <div className="route-loader">
      <span className="loading-spinner" />
      <span>Loading SmartHire...</span>
    </div>
  );
}

function NotFound() {
  return (
    <div className="not-found">
      <span>404</span>

      <h1>Page not found</h1>

      <p>The page you're looking for doesn't exist.</p>

      <a href="/dashboard" className="button secondary">
        Go to Dashboard
      </a>
    </div>
  );
}

export default function App() {
  return (
    <Suspense fallback={<PageLoader />}>
      <Routes>
        {/* =====================================================
            PUBLIC
            ===================================================== */}

        <Route path="/" element={<Landing />} />

        {/* =====================================================
            ONBOARDING
            ===================================================== */}

        <Route
          path="/onboarding"
          element={
            <Protected>
              <Onboarding />
            </Protected>
          }
        />

        <Route
          element={
            <Protected>
              <ProfileRequired>
                <WorkspaceLayout />
              </ProfileRequired>
            </Protected>
          }
        >
          {/* Dashboard */}
          <Route path="/dashboard" element={<Dashboard />} />

          {/* Resume Analysis */}
          <Route path="/analyze" element={<Analyze />} />

          {/* Analysis History */}
          <Route path="/history" element={<History />} />

          {/* Analysis Details */}
          <Route path="/analysis/:id" element={<Analysis />} />

          {/* AI Settings */}
          <Route path="/settings" element={<AISettings />} />
          <Route path="/jobs" element={<Job />} />
          <Route path="/interview-prep" element={<InterviewPrep />} />
          <Route path="/resources" element={<Resources />} />
        </Route>

        <Route path="*" element={<NotFound />} />
      </Routes>
    </Suspense>
  );
}
