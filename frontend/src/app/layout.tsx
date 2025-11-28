import type { Metadata } from 'next';
import { Inter } from 'next/font/google';
import { Toaster } from 'sonner';
import { AuthProvider } from '@/contexts/AuthContext';
import { ChatProvider } from '@/contexts/ChatContext';
import '@/styles/globals.css';

const inter = Inter({ subsets: ['latin'], variable: '--font-inter' });

export const metadata: Metadata = {
  title: 'AI Trading Predictor',
  description: 'Multi-agent AI system for trading predictions',
  keywords: ['trading', 'AI', 'predictions', 'crypto', 'stocks'],
};

export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <html lang="en" suppressHydrationWarning>
      <body className={`${inter.variable} font-sans antialiased`}>
        <AuthProvider>
          <ChatProvider>
            {children}
            <Toaster position="top-right" richColors />
          </ChatProvider>
        </AuthProvider>
      </body>
    </html>
  );
}
