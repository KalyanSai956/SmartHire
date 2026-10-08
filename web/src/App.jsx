import { lazy, Suspense } from "react";
import { Route, Routes } from "react-router-dom";
import BackendWakeup from "./components/BackendWakeup";
import ProtectedRoute from "./components/ProtectedRoute";
import ProfileRequired from "./components/ProfileRequired";
import WorkspaceLayout from "./components/WorkspaceLayout";
import Job from "./pages/Jobs";
import AISettings from "./pages/AISettings";
import Resources from "./pages/Resources";
import InterviewPrep from "./pages/InterviewPrep";
import Admin from "./pages/Admin";

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
    <BackendWakeup>
      <Suspense fallback={<PageLoader />}>
        <Routes>
          <Route path="/" element={<Landing />} />

          <Route
            path="/onboarding"
            element={
              <Protected>
                <Onboarding />
              </Protected>
            }
          />

          <Route
            path="/admin"
            element={
              <Protected>
                <Admin />
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
            <Route path="/dashboard" element={<Dashboard />} />
            <Route path="/analyze" element={<Analyze />} />
            <Route path="/history" element={<History />} />
            <Route path="/analysis/:id" element={<Analysis />} />
            <Route path="/settings" element={<AISettings />} />
            <Route path="/jobs" element={<Job />} />
            <Route path="/interview-prep" element={<InterviewPrep />} />
            <Route path="/resources" element={<Resources />} />
          </Route>

          <Route path="*" element={<NotFound />} />
        </Routes>
      </Suspense>
    </BackendWakeup>
  );
}
