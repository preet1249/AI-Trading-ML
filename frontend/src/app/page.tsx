import Link from 'next/link';

export default function HomePage() {
  return (
    <main className="flex min-h-screen flex-col items-center justify-center bg-gradient-to-b from-slate-900 to-slate-800 p-24">
      <div className="text-center space-y-8">
        <h1 className="text-5xl font-bold text-white mb-4">
          AI Trading Predictor
        </h1>
        <p className="text-xl text-slate-300 max-w-2xl">
          Multi-agent AI system powered by LangGraph and Qwen 3 for real-time
          trading predictions with ICT/SMC analysis.
        </p>
        <div className="flex gap-4 justify-center mt-8">
          <Link
            href="/auth/login"
            className="px-6 py-3 bg-blue-600 hover:bg-blue-700 text-white rounded-lg font-semibold transition-colors"
          >
            Login
          </Link>
          <Link
            href="/auth/signup"
            className="px-6 py-3 bg-slate-700 hover:bg-slate-600 text-white rounded-lg font-semibold transition-colors"
          >
            Sign Up
          </Link>
        </div>
      </div>
    </main>
  );
}
