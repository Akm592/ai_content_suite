// frontend/app/page.tsx
import Link from 'next/link';

export default function HomePage() {
  return (
    <main className="flex min-h-screen flex-col items-center justify-center bg-gray-900 text-white p-24">
      <div className="text-center">
        <h1 className="text-5xl font-bold mb-4">AI Content Transformation Suite</h1>
        <p className="text-xl text-gray-400 mb-12">Choose a tool to get started.</p>
        <div className="flex justify-center gap-8">
          <Link href="/audiobook" className="px-8 py-4 bg-blue-600 rounded-lg text-lg font-semibold hover:bg-blue-700 transition-colors">
            PDF to Audiobook
          </Link>
          <Link href="/storybook" className="px-8 py-4 bg-purple-600 rounded-lg text-lg font-semibold hover:bg-purple-700 transition-colors">
            AI Storybook Creator
          </Link>
        </div>
      </div>
    </main>
  );
}