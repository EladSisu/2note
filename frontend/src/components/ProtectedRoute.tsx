import { Navigate } from 'react-router-dom';
import { useAuth } from '../contexts/useAuth';

export function ProtectedRoute({ children }: { children: React.ReactNode }) {
  const { isAuthenticated, loading } = useAuth();

  if (loading) {
    return <div>Loading...</div>;
  }

  if (!isAuthenticated) {
    return <Navigate to="/auth" />;
  }

  return <>{children}</>;
}