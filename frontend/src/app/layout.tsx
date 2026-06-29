import type { Metadata } from 'next';
import { Noto_Sans_KR } from 'next/font/google';
import './globals.css';
import Nav from '@/components/Nav';
import Footer from '@/components/Footer';

const noto = Noto_Sans_KR({
  subsets: ['latin'],
  weight: ['400', '500', '600', '700'],
  variable: '--font-noto',
  display: 'swap',
});

export const metadata: Metadata = {
  title: '팜가드 AI - 농업 리스크 코치',
  description: '필지 단위 병해충, 기상 리스크 예측 및 행동 권고',
};

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="ko" className={noto.variable}>
      <body className="page-shell font-sans">
        <Nav />
        <main className="page-main">{children}</main>
        <Footer />
      </body>
    </html>
  );
}
