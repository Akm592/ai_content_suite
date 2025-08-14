// frontend/app/storybook/edit/[sessionId]/page.tsx
'use client';

import { useEffect, useState, useCallback, useRef } from 'react';
import { useParams } from 'next/navigation';
import Image from 'next/image'; // New import
import PdfPreviewModal from '../../../components/ui/PdfPreviewModal';

// Define types for our session data for type safety
interface Scene {
  text: string;
  image_url: string | null;
}
interface Styles {
  font_name: string;
  font_size: number;
}
interface StorybookSession {
  session_id: string;
  styles: Styles;
  scenes: Scene[];
  title: string;
  author: string;
}

// Debounce helper function to delay API calls
function debounce<F extends (...args: Parameters<F>) => Promise<void>>(func: F, waitFor: number) {
  let timeout: NodeJS.Timeout;
  return (...args: Parameters<F>): Promise<void> => {
    return new Promise(resolve => {
      if (timeout) clearTimeout(timeout);
      timeout = setTimeout(() => {
        func(...args).then(resolve); // Resolve the outer promise when the debounced function completes
      }, waitFor);
    });
  };
}

export default function EditStorybookPage() {
  const params = useParams();
  const sessionId = params.sessionId as string;

  const [session, setSession] = useState<StorybookSession | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState('');
  const [isPreviewing, setIsPreviewing] = useState(false);
  const [previewUrl, setPreviewUrl] = useState<string | null>(null); // This will hold a temporary blob: URL
  const [regeneratingScene, setRegeneratingScene] = useState<number | null>(null);
  const [storybookTitle, setStorybookTitle] = useState(''); // New state
  const [storybookAuthor, setStorybookAuthor] = useState(''); // New state
  const [currentFontName, setCurrentFontName] = useState('Helvetica'); // New state for font name
  const [currentFontSize, setCurrentFontSize] = useState(14); // New state for font size

  // Refs for debounced functions
  const saveTextChangesRef = useRef(debounce(async (_sceneIndex: number, _newText: string) => {}, 1000));
  const saveDetailsChangesRef = useRef(debounce(async (_newTitle: string, _newAuthor: string) => {}, 1000));
  const saveStyleChangesRef = useRef(debounce(async (_newFontName: string, _newFontSize: number) => {}, 1000));

  // Initialize debounced functions in a useEffect to ensure they are stable
  useEffect(() => {
    saveTextChangesRef.current = debounce(async (sceneIndex: number, newText: string) => {
      if (!sessionId) return;
      try {
        await fetch(`${process.env.NEXT_PUBLIC_API_URL}/storybook/session/${sessionId}/scene/${sceneIndex}`, {
          method: 'PUT',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ text: newText }),
        });
      } catch (err: unknown) {
          console.error("Failed to save text changes:", err);
      }
    }, 1000);

    saveDetailsChangesRef.current = debounce(async (newTitle: string, newAuthor: string) => {
      if (!sessionId) return;
      try {
        await fetch(`${process.env.NEXT_PUBLIC_API_URL}/storybook/session/${sessionId}/details`, {
          method: 'PUT',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ title: newTitle, author: newAuthor }),
        });
      } catch (err: unknown) {
          console.error("Failed to save story details:", err);
      }
    }, 1000);

    saveStyleChangesRef.current = debounce(async (newFontName: string, newFontSize: number) => {
      if (!sessionId) return;
      try {
        await fetch(`${process.env.NEXT_PUBLIC_API_URL}/storybook/session/${sessionId}/styles`, {
          method: 'PUT',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ font_name: newFontName, font_size: newFontSize }),
        });
      } catch (err: unknown) {
          console.error("Failed to save style changes:", err);
      }
    }, 1000);
  }, [sessionId]); // Depend on sessionId to recreate debounced functions if session changes

  // This effect runs once on mount to fetch the initial session data
  useEffect(() => {
    if (!sessionId) {
        setIsLoading(false);
        setError("Session ID not found in URL.");
        return;
    };

    const fetchSessionData = async () => {
      setIsLoading(true);
      try {
        const response = await fetch(`${process.env.NEXT_PUBLIC_API_URL}/storybook/session/${sessionId}/state`);
        if (!response.ok) {
          throw new Error('Could not load session. It may have expired or does not exist.');
        }
        const data = await response.json();
        setSession(data);
        setStorybookTitle(data.title || ''); // Populate title
        setStorybookAuthor(data.author || ''); // Populate author
        setCurrentFontName(data.styles.font_name || 'Helvetica'); // Populate font name
        setCurrentFontSize(data.styles.font_size || 14); // Populate font size
      } catch (err: unknown) {
        if (err instanceof Error) {
          setError(err.message);
        } else {
          setError("An unknown error occurred during session data fetch.");
        }
      } finally {
        setIsLoading(false);
      }
    };
    
    fetchSessionData();
  }, [sessionId]);

  // Handler for when the user types in a textarea
  const handleTextChange = (sceneIndex: number, newText: string) => {
    if (!session) return;
    const newSessionState = {...session, scenes: session.scenes.map((s, i) => i === sceneIndex ? {...s, text: newText} : s)};
    setSession(newSessionState); // Update UI immediately
    saveTextChangesRef.current(sceneIndex, newText); // Call via ref
  };

  // Handlers for title and author changes
  const handleTitleChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const newTitle = e.target.value;
    setStorybookTitle(newTitle);
    saveDetailsChangesRef.current(newTitle, storybookAuthor); // Call via ref
  };

  const handleAuthorChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const newAuthor = e.target.value;
    setStorybookAuthor(newAuthor);
    saveDetailsChangesRef.current(storybookTitle, newAuthor); // Call via ref
  };

  // Handlers for font style changes
  const handleFontNameChange = (e: React.ChangeEvent<HTMLSelectElement>) => {
    const newFontName = e.target.value;
    setCurrentFontName(newFontName);
    saveStyleChangesRef.current(newFontName, currentFontSize); // Call via ref
  };

  const handleFontSizeChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const newFontSize = parseInt(e.target.value);
    if (!isNaN(newFontSize)) {
      setCurrentFontSize(newFontSize);
      saveStyleChangesRef.current(currentFontName, newFontSize); // Call via ref
    }
  };

  // Handler for regenerating an image
  const handleRegenerateImage = async (sceneIndex: number) => {
    if (!session) return;
    setRegeneratingScene(sceneIndex);
    try {
      const response = await fetch(`${process.env.NEXT_PUBLIC_API_URL}/storybook/session/${sessionId}/scene/${sceneIndex}/regenerate`, { method: 'POST' });
      if (!response.ok) throw new Error("Failed to regenerate image.");
      const data = await response.json();
      const newSessionState = {...session, scenes: session.scenes.map((s, i) => i === sceneIndex ? {...s, image_url: data.new_image_url} : s)};
      setSession(newSessionState);
    } catch (err: unknown) {
      if (err instanceof Error) {
        setError(err.message);
      } else {
        setError("An unknown error occurred during image regeneration.");
      }
    } finally {
      setRegeneratingScene(null);
    }
  };

  // Handler for the "Preview Storybook" button
  const handlePreview = async () => {
    if (!sessionId) return;
    setIsPreviewing(true);
    setError('');
    try {
      const response = await fetch(`${process.env.NEXT_PUBLIC_API_URL}/storybook/session/${sessionId}/preview`);
      if (!response.ok) {
        const errData = await response.json();
        throw new Error(errData.detail || 'Failed to generate preview.');
      }
      
      const pdfBlob = await response.blob();
      // Create a temporary, local URL for the blob data
      const objectUrl = URL.createObjectURL(pdfBlob);
      setPreviewUrl(objectUrl); // This triggers the modal to open

    } catch (err: unknown) {
      if (err instanceof Error) {
        setError(err.message);
      } else {
        setError("An unknown error occurred during preview generation.");
      }
    } finally {
      setIsPreviewing(false);
    }
  };
  
  // Callback function passed to the modal to clean up when it closes
  const onModalClose = () => {
    // Revoke the temporary URL to free up browser memory
    if (previewUrl) {
      URL.revokeObjectURL(previewUrl);
    }
    setPreviewUrl(null);
  };

  if (isLoading) return <div className="text-center p-12 text-xl">Loading Your Storybook Editor...</div>;
  if (error) return <div className="text-center p-12 text-xl text-red-500">Error: {error}</div>;
  if (!session) return <div className="text-center p-12 text-xl">Session not found. Please <a href="/storybook" className="text-blue-400 font-semibold hover:underline">start a new session</a>.</div>;

  return (
<>
  <main className="min-h-screen p-6 bg-gradient-to-br from-black via-zinc-900 to-neutral-900 relative overflow-hidden">
    {/* Background glow accents */}
    <div className="absolute -top-40 -left-40 w-[500px] h-[500px] bg-purple-900/20 rounded-full blur-3xl"></div>
    <div className="absolute -bottom-40 -right-40 w-[400px] h-[400px] bg-indigo-900/20 rounded-full blur-3xl"></div>

    {/* Top Bar */}
    <div className="flex flex-col sm:flex-row justify-between items-center mb-8 sticky top-0 backdrop-blur-md bg-black/30 py-4 z-10 px-4 rounded-b-2xl border-b border-white/10 shadow-lg">
      <h1 className="text-3xl font-bold text-white drop-shadow-md">🎨 Edit Your Storybook</h1>
      <button
        onClick={handlePreview}
        disabled={isPreviewing}
        className="bg-gradient-to-r from-purple-700 to-indigo-800 hover:from-purple-800 hover:to-indigo-900 text-white font-bold py-2 px-5 rounded-xl shadow-lg transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
      >
        {isPreviewing ? 'Generating Preview...' : '📖 Preview Storybook'}
      </button>
    </div>

    {/* Title and Author Inputs */}
    <div className="mb-8 p-6 bg-black/40 border border-white/10 backdrop-blur-xl rounded-3xl shadow-2xl">
      <h3 className="text-xl font-semibold mb-3 text-purple-300 drop-shadow-md">
        📚 Story Details
      </h3>
      <div className="mb-4">
        <label htmlFor="storybook-title" className="block text-sm font-medium text-gray-300 mb-2">
          Story Title
        </label>
        <input
          type="text"
          id="storybook-title"
          value={storybookTitle}
          onChange={handleTitleChange}
          className="w-full p-3 bg-black/30 border border-white/10 text-white placeholder:text-gray-500 rounded-xl focus:ring-2 focus:ring-purple-500 transition-all"
          placeholder="Enter your story's title"
        />
      </div>
      <div>
        <label htmlFor="storybook-author" className="block text-sm font-medium text-gray-300 mb-2">
          Author Name
        </label>
        <input
          type="text"
          id="storybook-author"
          value={storybookAuthor}
          onChange={handleAuthorChange}
          className="w-full p-3 bg-black/30 border border-white/10 text-white placeholder:text-gray-500 rounded-xl focus:ring-2 focus:ring-purple-500 transition-all"
          placeholder="Enter the author's name"
        />
      </div>
    </div>

    {/* Style Settings */}
    <div className="mb-8 p-6 bg-black/40 border border-white/10 backdrop-blur-xl rounded-3xl shadow-2xl">
      <h3 className="text-xl font-semibold mb-3 text-purple-300 drop-shadow-md">
        🎨 Style Settings
      </h3>
      <div className="mb-4">
        <label htmlFor="font-name" className="block text-sm font-medium text-gray-300 mb-2">
          Font Name
        </label>
        <select
          id="font-name"
          value={currentFontName}
          onChange={handleFontNameChange}
          className="w-full p-3 bg-black/30 border border-white/10 text-white rounded-xl focus:ring-2 focus:ring-purple-500 transition-all"
        >
          <option value="Helvetica">Helvetica</option>
          <option value="Times-Roman">Times-Roman</option>
          <option value="Courier">Courier</option>
        </select>
      </div>
      <div>
        <label htmlFor="font-size" className="block text-sm font-medium text-gray-300 mb-2">
          Font Size
        </label>
        <input
          type="number"
          id="font-size"
          value={currentFontSize}
          onChange={handleFontSizeChange}
          min="8"
          max="36"
          className="w-full p-3 bg-black/30 border border-white/10 text-white rounded-xl focus:ring-2 focus:ring-purple-500 transition-all"
        />
      </div>
    </div>

    {/* Scene List */}
    <div className="space-y-10">
      {session.scenes.map((scene, index) => (
        <div
          key={index}
          className="p-6 bg-black/40 border border-white/10 backdrop-blur-xl rounded-3xl shadow-2xl"
        >
          <h3 className="text-xl font-semibold mb-3 text-purple-300 drop-shadow-md">
            ✨ Scene {index + 1}
          </h3>

          {/* Scene Textarea */}
          <textarea
            value={scene.text}
            onChange={(e) => handleTextChange(index, e.target.value)}
            className="w-full p-4 bg-black/30 border border-white/10 text-white placeholder:text-gray-500 rounded-xl focus:ring-2 focus:ring-purple-500 transition-all resize-none"
            rows={6}
            placeholder="Describe the scene here..."
          />

          {/* Image Preview */}
          <div className="mt-6 relative aspect-square max-w-md mx-auto bg-black/30 border border-white/10 rounded-2xl flex items-center justify-center overflow-hidden">
            {scene.image_url ? (
              <Image // Changed from img
                src={`${process.env.NEXT_PUBLIC_API_URL}${scene.image_url}`}
                alt={`Illustration for scene ${index + 1}`}
                fill // Added fill prop
                style={{ objectFit: 'contain' }} // Added style prop for object-fit
                className="rounded-2xl" // Kept relevant class
              />
            ) : (
              <div className="text-gray-400">No image generated</div>
            )}

            {/* Regenerate Button */}
            <button
              onClick={() => handleRegenerateImage(index)}
              disabled={regeneratingScene === index}
              className="absolute bottom-3 right-3 bg-gradient-to-r from-indigo-600 to-blue-700 hover:from-indigo-700 hover:to-blue-800 text-white p-3 rounded-full shadow-lg transition-transform hover:scale-110 disabled:opacity-50 disabled:cursor-not-allowed"
              title="Regenerate Image"
            >
              {regeneratingScene === index ? (
                <div className="w-5 h-5 border-2 border-t-transparent border-white rounded-full animate-spin"></div>
              ) : (
                '🔄'
              )}
            </button>
          </div>
        </div>
      ))}
    </div>
  </main>

  {/* PDF Preview Modal */}
  {previewUrl && (
    <PdfPreviewModal
      sessionId={sessionId}
      pdfUrl={previewUrl}
      onClose={onModalClose}
    />
  )}
</>

  );
}