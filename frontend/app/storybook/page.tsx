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
  const [pdfFile, setPdfFile] = useState<File | null>(null); // New state for PDF file
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState('');
  const router = useRouter();

  const handleFileChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    if (e.target.files && e.target.files[0]) {
      setPdfFile(e.target.files[0]);
      setStoryText(''); // Clear story text if PDF is selected
    } else {
      setPdfFile(null);
    }
  };

  const handleStoryTextChange = (e: React.ChangeEvent<HTMLTextAreaElement>) => {
    setStoryText(e.target.value);
    setPdfFile(null); // Clear PDF if story text is entered
  };

  const handleFormAction = async (action: 'direct' | 'edit', e: React.FormEvent) => {
    e.preventDefault();
    // Validation: Either storyText or pdfFile must be present
    if (!storyText && !pdfFile) {
      setError('Please provide either story text or a PDF file.');
      return;
    }
    if (!characterDesc || !styleDesc) {
      setError('Please fill out character and style descriptions.');
      return;
    }
    setIsLoading(true);
    setError('');

    const formData = new FormData();
    if (pdfFile) {
      formData.append('pdf_file', pdfFile);
    } else {
      formData.append('story_text', storyText);
    }
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
    } catch (err: unknown) {
      if (err instanceof Error) {
        setError(err.message);
      } else {
        setError("An unknown error occurred.");
      }
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
                Your Story Text (or upload a PDF)
              </label>
              <Textarea
                id="story"
                value={storyText}
                onChange={handleStoryTextChange} // Use the new handler
                rows={6}
                className="bg-black/40 border-white/10 text-white placeholder:text-gray-500 focus:ring-2 focus:ring-purple-500"
                placeholder="Once upon a time, in a land filled with candy..."
                disabled={!!pdfFile} // Disable if PDF is selected
              />
            </div>

            <div className="mt-4">
              <label htmlFor="pdf-upload" className="block text-sm font-medium text-gray-300 mb-2">
                Upload PDF
              </label>
              <Input
                id="pdf-upload"
                type="file"
                accept=".pdf"
                onChange={handleFileChange} // Use the new handler
                className="bg-black/40 border-white/10 text-white file:text-white file:bg-purple-700 file:border-none file:rounded-md file:py-2 file:px-4 file:mr-4 hover:file:bg-purple-800"
              />
              {pdfFile && <p className="text-gray-400 text-sm mt-2">Selected: {pdfFile.name}</p>}
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
