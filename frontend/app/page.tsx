import Link from 'next/link';
import { ThemeToggle } from '../components/theme-toggle';

export default function HomePage() {
  return (
    <main className="relative min-h-screen flex flex-col items-center justify-center bg-background overflow-hidden p-8">
      {/* Theme Toggle */}
      <div className="absolute top-4 right-4 z-20">
        <ThemeToggle />
      </div>

      {/* Background glow accents */}
      <div className="absolute -top-40 -left-40 w-[500px] h-[500px] bg-purple-900/20 rounded-full blur-3xl"></div>
      <div className="absolute -bottom-40 -right-40 w-[400px] h-[400px] bg-indigo-900/20 rounded-full blur-3xl"></div>

      <div className="relative z-10 text-center max-w-3xl">
        <h1 className="text-5xl sm:text-6xl font-bold mb-6 text-foreground drop-shadow-md">
          AI Content Transformation Suite
        </h1>
        <p className="text-lg sm:text-xl text-muted-foreground mb-12">
          Choose a tool to unleash your creativity.
        </p>

        <div className="flex flex-col sm:flex-row justify-center gap-6">
          <Link
            href="/audiobook"
            className="flex-1 bg-primary text-primary-foreground font-bold py-4 px-8 rounded-2xl shadow-lg text-lg transition-all hover:scale-105 text-center"
          >
             PDF to Audiobook
          </Link>
          <Link
            href="/storybook"
            className="flex-1 bg-secondary text-secondary-foreground font-bold py-4 px-8 rounded-2xl shadow-lg text-lg transition-all hover:scale-105 text-center"
          >
             AI Storybook Creator
          </Link>
        </div>
      </div>
    </main>
  );
}
