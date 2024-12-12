import { Link } from 'react-router-dom';
import { useAuth } from '../contexts/AuthContext';

export default function LandingPage() {
  const { isAuthenticated } = useAuth();

  return (
    <div className="min-h-screen bg-white">
      <nav className="fixed top-0 left-0 right-0 bg-white border-b">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="flex justify-between items-center h-16">
            <h1 className="text-xl font-bold">NotesShare</h1>
            <div>
              {isAuthenticated ? (
                <Link
                  to="/documents"
                  className="ml-4 px-4 py-2 rounded-md bg-black text-white hover:bg-black/90"
                >
                  Dashboard
                </Link>
              ) : (
                <Link
                  to="/auth"
                  className="ml-4 px-4 py-2 rounded-md bg-black text-white hover:bg-black/90"
                >
                  Sign In
                </Link>
              )}
            </div>
          </div>
        </div>
      </nav>

      <main className="pt-16">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-20">
          <div className="text-center">
            <h2 className="text-4xl font-bold text-gray-900 sm:text-6xl">
              Collaborative Document Editing
            </h2>
            <p className="mt-6 text-lg text-gray-600">
              Create, edit, and share documents in real-time with your team.
            </p>
            <div className="mt-10">
              <Link
                to={isAuthenticated ? "/documents" : "/auth"}
                className="px-8 py-3 rounded-md bg-black text-white hover:bg-black/90"
              >
                Get Started
              </Link>
            </div>
          </div>
        </div>
      </main>
    </div>
  );
}