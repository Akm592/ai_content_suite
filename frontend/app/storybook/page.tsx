// frontend/app/storybook/page.tsx
'use client';

import { useState } from 'react';

export default function StorybookCreatorPage() {
  const [story, setStory] = useState('');
  const [character, setCharacter] = useState('');
  const [style, setStyle] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!story || !character || !style) {
      setError("Please fill out all fields.");
      return;
    }

    setIsLoading(true);
    setError(null);

    const formData = new FormData();
    formData.append('story_text', story);
    formData.append('character_desc', character);
    formData.append('style_desc', style);

    try {
      const response = await fetch('http://127.0.0.1:8000/storybook/create', {
        method: 'POST',
        body: formData,
      });

      if (!response.ok) {
        const errData = await response.json();
        throw new Error(errData.detail || "Failed to create storybook.");
      }

      const blob = await response.blob();
      const url = window.URL.createObjectURL(blob);
      const a = document.createElement('a');
      a.href = url;
      a.download = 'ai_storybook.pdf';
      document.body.appendChild(a);
      a.click();
      a.remove();
      window.URL.revokeObjectURL(url);

    } catch (err: any) {
      setError(err.message);
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <main className="flex min-h-screen flex-col items-center p-12 bg-gray-900 text-white">
      <h1 className="text-4xl font-bold mb-8">AI Storybook Creator</h1>
      <form onSubmit={handleSubmit} className="w-full max-w-lg bg-gray-800 p-8 rounded-lg">
        <div className="mb-6">
          <label htmlFor="story" className="block mb-2 text-sm font-medium text-gray-300">Your Story</label>
          <textarea id="story" value={story} onChange={e => setStory(e.target.value)} rows={10} className="bg-gray-700 border border-gray-600 text-white text-sm rounded-lg block w-full p-2.5" placeholder="Once upon a time..."></textarea>
        </div>
        <div className="mb-6">
          <label htmlFor="character" className="block mb-2 text-sm font-medium text-gray-300">Character Description</label>
          <input type="text" id="character" value={character} onChange={e => setCharacter(e.target.value)} className="bg-gray-700 border border-gray-600 text-white text-sm rounded-lg block w-full p-2.5" placeholder="e.g., A brave fox with a tiny hat" />
        </div>
        <div className="mb-6">
          <label htmlFor="style" className="block mb-2 text-sm font-medium text-gray-300">Art Style</label>
          <input type="text" id="style" value={style} onChange={e => setStyle(e.target.value)} className="bg-gray-700 border border-gray-600 text-white text-sm rounded-lg block w-full p-2.5" placeholder="e.g., Vibrant watercolor painting" />
        </div>
        <button type="submit" disabled={isLoading} className="w-full text-white bg-purple-600 hover:bg-purple-700 focus:ring-4 focus:outline-none focus:ring-purple-800 font-medium rounded-lg text-sm px-5 py-2.5 text-center disabled:bg-gray-500">
          {isLoading ? 'Creating Your Storybook...' : 'Create Storybook'}
        </button>
        {isLoading && <p className="mt-4 text-yellow-400 text-center">This can take several minutes depending on the story length...</p>}
        {error && <p className="mt-4 text-red-500 text-center">{error}</p>}
      </form>
    </main>
  );
}
