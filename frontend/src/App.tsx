import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom';
import { Toaster } from 'react-hot-toast';
import Sidebar from './components/Sidebar';
import Dashboard from './pages/Dashboard';
import Agents from './pages/Agents';
import CallLogs from './pages/CallLogs';
import Settings from './pages/Settings';

function App() {
  return (
    <BrowserRouter>
      <div className="flex h-screen overflow-hidden bg-surface text-textPrimary font-sans">
        <Sidebar />
        <main className="flex-1 overflow-y-auto p-8 border-l border-border bg-bg">
          <Routes>
            <Route path="/dashboard" element={<Dashboard />} />
            <Route path="/agents" element={<Agents />} />
            <Route path="/logs" element={<CallLogs />} />
            <Route path="/settings" element={<Settings />} />
            <Route path="*" element={<Navigate to="/dashboard" replace />} />
          </Routes>
        </main>
      </div>
      <Toaster position="top-right" />
    </BrowserRouter>
  );
}

export default App;
