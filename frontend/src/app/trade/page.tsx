'use client';

import ChatPanel from '@/components/ChatPanel';
import ChatHistorySidebar from '@/components/ChatHistorySidebar';
import TradingViewChart from '@/components/TradingViewChart';
import ProtectedRoute from '@/components/ProtectedRoute';
import { useAuth } from '@/contexts/AuthContext';

export default function TradePage() {
  const { user, logout } = useAuth();

  return (
    <ProtectedRoute>
      <div className="h-screen bg-black flex flex-col">
        {/* Header */}
        <header className="border-b border-zinc-800 bg-zinc-900/50 backdrop-blur-sm">
          <div className="px-6 py-4 flex items-center justify-between">
            <div className="flex items-center gap-4">
              <h1 className="text-xl font-bold text-white">AI Trading Predictor</h1>
            </div>

            {/* User Menu */}
            <div className="flex items-center gap-3">
              <span className="text-sm text-gray-400">{user?.email}</span>
              <button
                onClick={logout}
                className="px-4 py-2 text-sm bg-gray-800 hover:bg-gray-700 text-white rounded-lg transition"
              >
                Logout
              </button>
            </div>
          </div>
        </header>

        {/* Main Content: Sidebar (20%) + Chat (30%) + Chart (50%) */}
        <div className="flex-1 flex overflow-hidden">
          {/* Chat History Sidebar - 20% */}
          <div className="w-[20%]">
            <ChatHistorySidebar />
          </div>

          {/* Chat Panel - 30% */}
          <div className="w-[30%] border-r border-zinc-800">
            <ChatPanel />
          </div>

          {/* Chart Panel - 50% */}
          <div className="w-[50%]">
            <TradingViewChart />
          </div>
        </div>
      </div>
    </ProtectedRoute>
  );
}
