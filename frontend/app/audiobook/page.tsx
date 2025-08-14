'use client';

import { useState } from 'react';

const voiceProfiles = [
  "AMERICAN_MALE", "AMERICAN_FEMALE", "BRITISH_MALE", "BRITISH_FEMALE"
];

export default function AudiobookConverterPage() {
  const [file, setFile] = useState<File | null>(null);
  const [voice, setVoice] = useState(voiceProfiles[0]);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const handleFileChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    if (e.target.files && e.target.files.length > 0) {
      setFile(e.target.files[0]);
    }
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!file) {
      setError("Please select a PDF file first.");
      return;
    }

    setIsLoading(true);
    setError(null);

    const formData = new FormData();
    formData.append('pdf_file', file);
    formData.append('voice', voice);

    try {
      const response = await fetch('http://127.0.0.1:8000/audiobook/convert', {
        method: 'POST',
        body: formData,
      });

      if (!response.ok) {
        const errData = await response.json();
        throw new Error(errData.detail || "An unknown error occurred.");
      }

      const blob = await response.blob();
      const url = window.URL.createObjectURL(blob);
      const a = document.createElement('a');
      a.href = url;
      a.download = 'audiobook.mp3';
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
    <main className="relative min-h-screen flex flex-col items-center justify-center bg-gradient-to-br from-black via-zinc-900 to-neutral-900 overflow-hidden p-6">
      {/* Glow accents */}
      <div className="absolute -top-40 -left-40 w-[500px] h-[500px] bg-blue-900/20 rounded-full blur-3xl"></div>
      <div className="absolute -bottom-40 -right-40 w-[400px] h-[400px] bg-cyan-900/20 rounded-full blur-3xl"></div>

      <div className="w-full max-w-lg shadow-2xl border border-white/5 backdrop-blur-xl bg-black/40 rounded-3xl p-8 relative z-10">
        <h1 className="text-4xl font-bold mb-6 text-center text-white drop-shadow-md">
           PDF to Audiobook Converter
        </h1>

        <form onSubmit={handleSubmit} className="space-y-6">
          {/* File Upload */}
          <div>
            <label htmlFor="file" className="block mb-2 text-sm font-medium text-gray-300">
              Upload PDF
            </label>
            <input
              type="file"
              id="file"
              onChange={handleFileChange}
              accept=".pdf"
              className="bg-black/40 border border-white/10 text-white text-sm rounded-lg focus:ring-2 focus:ring-blue-500 block w-full p-2.5 placeholder:text-gray-500"
            />
          </div>

          {/* Voice Selection */}
          <div>
            <label htmlFor="voice" className="block mb-2 text-sm font-medium text-gray-300">
              Select Voice
            </label>
            <select
              id="voice"
              value={voice}
              onChange={(e) => setVoice(e.target.value)}
              className="bg-black/40 border border-white/10 text-white text-sm rounded-lg focus:ring-2 focus:ring-blue-500 block w-full p-2.5"
            >
              {voiceProfiles.map(v => (
                <option key={v} value={v}>
                  {v.replace(/_/g, " ")}
                </option>
              ))}
            </select>
          </div>

          {/* Submit Button */}
          <button
            type="submit"
            disabled={isLoading || !file}
            className="w-full bg-gradient-to-r from-blue-700 to-cyan-800 hover:from-blue-800 hover:to-cyan-900 text-white font-bold py-3 rounded-xl shadow-lg transition-all disabled:opacity-50 disabled:cursor-not-allowed"
          >
            {isLoading ? 'Converting...' : ' Convert to Audiobook'}
          </button>

          {/* Error Message */}
          {error && (
            <p className="text-red-400 text-center font-medium bg-red-900/20 p-2 rounded-lg border border-red-900/40">
              {error}
            </p>
          )}
        </form>
      </div>
    </main>
  );
}
