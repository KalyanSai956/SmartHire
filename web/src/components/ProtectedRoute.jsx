import { Navigate, useLocation } from "react-router-dom";
import { useAuth } from "../context/AuthContext";
import "../CSS/ProtectedRoute.css";
export default function ProtectedRoute({ children }) {
  const { session, loading } = useAuth();
  const location = useLocation();

  if (loading) {
    return (
      <div className="route-loader">
        <span className="loading-spinner" />
        <span>Loading SmartHire...</span>
      </div>
    );
  }

  if (!session) {
    return <Navigate to="/" replace state={{ from: location.pathname }} />;
  }

  return children;
}
