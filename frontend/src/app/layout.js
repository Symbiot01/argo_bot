import './globals.scss';
import DynamicBackground from '../components/layout/DynamicBackground';

export const metadata = {
  title: 'Ocean AI Analytics',
  description: 'An immersive interface for interacting with a powerful AI.',
};

export default function RootLayout({ children }) {
  return (
    <html lang="en">
      <body suppressHydrationWarning={true}>
        <DynamicBackground />
        {children}
      </body>
    </html>
  );
}