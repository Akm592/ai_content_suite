'use client';

import { useState } from 'react';
import { useRouter } from 'next/navigation';
import { Input } from '@/components/ui/input';
import { Textarea } from '@/components/ui/textarea';
import { Button } from '@/components/ui/button';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';

export default function StorybookCreatorStartPage() {
  const [storyText, setStoryText] = useState('');
  const [characterDesc, setCharacterDesc] = useState('');
  const [styleDesc, setStyleDesc] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState('');
  const router = useRouter();

  const handleFormAction = async (action: 'direct' | 'edit', e: React.FormEvent) => {
    e.preventDefault();
    if (!storyText || !characterDesc || !styleDesc) {
      setError('Please fill out all fields.');
      return;
    }
    setIsLoading(true);
    setError('');

    const formData = new FormData();
    formData.append('story_text', storyText);
    formData.append('character_desc', characterDesc);
    formData.append('style_desc', styleDesc);

    try {
      if (action === 'direct') {
        const response = await fetch(`${process.env.NEXT_PUBLIC_API_URL}/storybook/create-and-finalize`, {
          method: 'POST',
          body: formData,
        });
        if (!response.ok) {
          const errData = await response.json();
          throw new Error(errData.detail || 'Failed to generate the storybook.');
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
      } else {
        const response = await fetch(`${process.env.NEXT_PUBLIC_API_URL}/storybook/session/start`, {
          method: 'POST',
          body: formData,
        });
        if (!response.ok) {
          const errData = await response.json();
          throw new Error(errData.detail || 'Failed to start an editing session.');
        }
        const sessionData = await response.json();
        localStorage.setItem(`storybook_session_${sessionData.session_id}`, JSON.stringify(sessionData));
        router.push(`/storybook/edit/${sessionData.session_id}`);
      }
    } catch (err: any) {
      setError(err.message);
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <main
      className="min-h-screen flex items-center justify-center p-6 bg-gradient-to-br from-black via-zinc-900 to-neutral-900 relative overflow-hidden"
    >
      {/* Subtle glow accents */}
      <div className="absolute -top-40 -left-40 w-[500px] h-[500px] bg-purple-900/20 rounded-full blur-3xl"></div>
      <div className="absolute -bottom-40 -right-40 w-[400px] h-[400px] bg-indigo-900/20 rounded-full blur-3xl"></div>

      <Card
        className="w-full max-w-3xl shadow-2xl border border-white/5 backdrop-blur-xl bg-black/40 rounded-3xl overflow-hidden"
      >
        <CardHeader className="text-center border-b border-white/10 bg-gradient-to-r from-zinc-900/80 to-neutral-800/80">
          <CardTitle className="text-4xl font-bold text-white drop-shadow-md">
             AI Storybook Creator
          </CardTitle>
          <p className="text-gray-400 mt-2 text-lg">
            Craft magical tales with vivid characters & beautiful illustrations.
          </p>
        </CardHeader>

        <CardContent className="p-6 space-y-6">
          <form className="space-y-6">
            <div>
              <label htmlFor="story" className="block text-sm font-medium text-gray-300 mb-2">
                Your Story Text
              </label>
              <Textarea
                id="story"
                value={storyText}
                onChange={e => setStoryText(e.target.value)}
                rows={6}
                className="bg-black/40 border-white/10 text-white placeholder:text-gray-500 focus:ring-2 focus:ring-purple-500"
                placeholder="Once upon a time, in a land filled with candy..."
              />
            </div>

            <div>
              <label htmlFor="character" className="block text-sm font-medium text-gray-300 mb-2">
                Character Description
              </label>
              <Input
                id="character"
                value={characterDesc}
                onChange={e => setCharacterDesc(e.target.value)}
                className="bg-black/40 border-white/10 text-white placeholder:text-gray-500 focus:ring-2 focus:ring-purple-500"
                placeholder="A friendly blue dragon with a tiny chef's hat."
              />
            </div>

            <div>
              <label htmlFor="style" className="block text-sm font-medium text-gray-300 mb-2">
                Artistic Style
              </label>
              <Input
                id="style"
                value={styleDesc}
                onChange={e => setStyleDesc(e.target.value)}
                className="bg-black/40 border-white/10 text-white placeholder:text-gray-500 focus:ring-2 focus:ring-purple-500"
                placeholder="Cozy watercolor, like a classic children's book."
              />
            </div>

            <div className="flex flex-col sm:flex-row gap-4 justify-center mt-8">
              <Button
                onClick={(e) => handleFormAction('direct', e)}
                disabled={isLoading}
                className="flex-1 bg-gradient-to-r from-purple-700 to-indigo-800 hover:from-purple-800 hover:to-indigo-900 text-white font-bold py-3 rounded-xl shadow-lg disabled:opacity-50 disabled:cursor-not-allowed"
              >
                {isLoading ? 'Generating...' : ' Quick Create & Download'}
              </Button>
              <Button
                onClick={(e) => handleFormAction('edit', e)}
                disabled={isLoading}
                className="flex-1 bg-gradient-to-r from-emerald-700 to-teal-800 hover:from-emerald-800 hover:to-teal-900 text-white font-bold py-3 rounded-xl shadow-lg disabled:opacity-50 disabled:cursor-not-allowed"
              >
                {isLoading ? 'Starting...' : 'Create & Edit Storybook'}
              </Button>
            </div>

            {error && (
              <p className="text-red-400 text-center font-medium bg-red-900/20 p-2 rounded-lg border border-red-900/40">
                {error}
              </p>
            )}
          </form>
        </CardContent>
      </Card>
    </main>
  );
}
