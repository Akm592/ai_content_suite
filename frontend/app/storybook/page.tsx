'use client';

import { useState } from 'react';
import { useRouter } from 'next/navigation';
import { Input } from '@/components/ui/input';
import { Textarea } from '@/components/ui/textarea';
import { Button } from '@/components/ui/button';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { ThemeToggle } from '@/components/theme-toggle'; // ✅ FIX: Added missing import

export default function StorybookCreatorStartPage() {
  const [storyText, setStoryText] = useState('');
  const [characterDesc, setCharacterDesc] = useState('');
  const [styleDesc, setStyleDesc] = useState('');
  const [pdfFile, setPdfFile] = useState<File | null>(null);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState('');
  const router = useRouter();

  const handleFileChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    if (e.target.files?.[0]) {
      setPdfFile(e.target.files[0]);
      setStoryText('');
    } else {
      setPdfFile(null);
    }
  };

  const handleStoryTextChange = (e: React.ChangeEvent<HTMLTextAreaElement>) => {
    setStoryText(e.target.value);
    setPdfFile(null);
  };

  const handleFormAction = async (
    action: 'direct' | 'edit',
    e?: React.FormEvent
  ) => {
    if (e) e.preventDefault();

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
    pdfFile
      ? formData.append('pdf_file', pdfFile)
      : formData.append('story_text', storyText);

    formData.append('character_desc', characterDesc);
    formData.append('style_desc', styleDesc);

    try {
      if (action === 'direct') {
        const response = await fetch(
          `${process.env.NEXT_PUBLIC_API_URL}/storybook/create-and-finalize`,
          { method: 'POST', body: formData }
        );

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
        const response = await fetch(
          `${process.env.NEXT_PUBLIC_API_URL}/storybook/session/start`,
          { method: 'POST', body: formData }
        );

        if (!response.ok) {
          const errData = await response.json();
          throw new Error(errData.detail || 'Failed to start an editing session.');
        }

        const sessionData = await response.json();
        localStorage.setItem(
          `storybook_session_${sessionData.session_id}`,
          JSON.stringify(sessionData)
        );
        router.push(`/storybook/edit/${sessionData.session_id}`);
      }
    } catch (err: unknown) {
      setError(err instanceof Error ? err.message : 'An unknown error occurred.');
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <main className="min-h-screen flex items-center justify-center p-6 bg-background relative overflow-hidden">
      {/* Theme Toggle */}
      <div className="absolute top-4 right-4 z-20">
        <ThemeToggle />
      </div>

      {/* Glow accents */}
      <div className="absolute -top-40 -left-40 w-[500px] h-[500px] bg-purple-900/20 rounded-full blur-3xl" />
      <div className="absolute -bottom-40 -right-40 w-[400px] h-[400px] bg-indigo-900/20 rounded-full blur-3xl" />

      <Card className="w-full max-w-3xl shadow-2xl border border-border backdrop-blur-xl bg-card rounded-3xl overflow-hidden">
        <CardHeader className="text-center border-b border-border bg-card-foreground/10">
          <CardTitle className="text-4xl font-bold text-foreground drop-shadow-md">
            AI Storybook Creator
          </CardTitle>
          <p className="text-muted-foreground mt-2 text-lg">
            Craft magical tales with vivid characters & beautiful illustrations.
          </p>
        </CardHeader>

        <CardContent className="p-6 space-y-6">
          <form className="space-y-6" onSubmit={(e) => e.preventDefault()}>
            <div>
              <label htmlFor="story" className="block text-sm font-medium text-muted-foreground mb-2">
                Your Story Text (or upload a PDF)
              </label>
              <Textarea
                id="story"
                value={storyText}
                onChange={handleStoryTextChange}
                rows={6}
                className="bg-input border-border text-foreground placeholder:text-muted-foreground focus:ring-2 focus:ring-primary"
                placeholder="Once upon a time, in a land filled with candy..."
                disabled={!!pdfFile}
              />
            </div>

            <div className="mt-4">
              <label htmlFor="pdf-upload" className="block text-sm font-medium text-muted-foreground mb-2">
                Upload PDF
              </label>
              <Input
                id="pdf-upload"
                type="file"
                accept=".pdf"
                onChange={handleFileChange}
                className="bg-input border-border text-foreground file:text-primary-foreground file:bg-primary file:border-none file:rounded-md file:py-2 file:px-4 file:mr-4 hover:file:bg-primary/90"
              />
              {pdfFile && <p className="text-muted-foreground text-sm mt-2">Selected: {pdfFile.name}</p>}
            </div>

            <div>
              <label htmlFor="character" className="block text-sm font-medium text-muted-foreground mb-2">
                Character Description
              </label>
              <Input
                id="character"
                value={characterDesc}
                onChange={(e) => setCharacterDesc(e.target.value)}
                className="bg-input border-border text-foreground placeholder:text-muted-foreground focus:ring-2 focus:ring-primary"
                placeholder="A friendly blue dragon with a tiny chef's hat."
              />
            </div>

            <div>
              <label htmlFor="style" className="block text-sm font-medium text-muted-foreground mb-2">
                Artistic Style
              </label>
              <Input
                id="style"
                value={styleDesc}
                onChange={(e) => setStyleDesc(e.target.value)}
                className="bg-input border-border text-foreground placeholder:text-muted-foreground focus:ring-2 focus:ring-primary"
                placeholder="Cozy watercolor, like a classic children's book."
              />
            </div>

            <div className="flex flex-col sm:flex-row gap-4 justify-center mt-8">
              <Button
                type="button"
                onClick={(e) => handleFormAction('direct', e)}
                disabled={isLoading}
                className="flex-1 bg-primary hover:bg-primary/90 text-primary-foreground font-bold py-3 rounded-xl shadow-lg disabled:opacity-50 disabled:cursor-not-allowed"
              >
                {isLoading ? 'Generating...' : 'Quick Create & Download'}
              </Button>
              <Button
                type="button"
                onClick={(e) => handleFormAction('edit', e)}
                disabled={isLoading}
                className="flex-1 bg-secondary hover:bg-secondary/90 text-secondary-foreground font-bold py-3 rounded-xl shadow-lg disabled:opacity-50 disabled:cursor-not-allowed"
              >
                {isLoading ? 'Starting...' : 'Create & Edit Storybook'}
              </Button>
            </div>

            {error && (
              <p className="text-destructive-foreground text-center font-medium bg-destructive/20 p-2 rounded-lg border border-destructive/40">
                {error}
              </p>
            )}
          </form>
        </CardContent>
      </Card>
    </main>
  );
}
