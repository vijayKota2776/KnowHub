import { Routes, Route, useLocation } from 'react-router-dom';
import { useAuth } from './context/AuthContext';
import Navbar from './components/Navbar';
import Sidebar from './components/Sidebar';
import ProtectedRoute from './components/ProtectedRoute';
import AuthPage from './pages/AuthPage';
import FeedPage from './pages/FeedPage';
import QuestionPage from './pages/QuestionPage';
import AskPage from './pages/AskPage';
import ProfilePage from './pages/ProfilePage';
import SearchPage from './pages/SearchPage';
import TopicsPage from './pages/TopicsPage';
import './App.css';

function AppLayout({ children }) {
  return (
    <div className="app-content">
      <Sidebar />
      <main className="main-content">
        {children}
      </main>
    </div>
  );
}

export default function App() {
  const { isAuthenticated } = useAuth();
  const location = useLocation();

  const isAuthPage = location.pathname === '/login';

  return (
    <div className="app">
      {!isAuthPage && <Navbar />}
      <div style={{ position: 'relative', zIndex: 1 }}>
        <Routes>
          <Route path="/login" element={<AuthPage />} />

          <Route
            path="/"
            element={
              <ProtectedRoute>
                <AppLayout><FeedPage /></AppLayout>
              </ProtectedRoute>
            }
          />
          <Route
            path="/question/:id"
            element={
              <AppLayout><QuestionPage /></AppLayout>
            }
          />
          <Route
            path="/ask"
            element={
              <ProtectedRoute>
                <AppLayout><AskPage /></AppLayout>
              </ProtectedRoute>
            }
          />
          <Route
            path="/profile/:id"
            element={
              <ProtectedRoute>
                <AppLayout><ProfilePage /></AppLayout>
              </ProtectedRoute>
            }
          />
          <Route
            path="/search"
            element={
              <AppLayout><SearchPage /></AppLayout>
            }
          />
          <Route
            path="/topics"
            element={
              <AppLayout><TopicsPage /></AppLayout>
            }
          />

          {/* 404 */}
          <Route path="*" element={
            <AppLayout>
              <div className="empty-state" style={{ marginTop: '60px' }}>
                <div className="empty-state-icon">🌌</div>
                <h3>Page not found</h3>
                <p>This page doesn't exist. Head back to the feed.</p>
                <a href="/" className="btn btn-primary" style={{ marginTop: '8px' }}>Go to Feed</a>
              </div>
            </AppLayout>
          } />
        </Routes>
      </div>
    </div>
  );
}
