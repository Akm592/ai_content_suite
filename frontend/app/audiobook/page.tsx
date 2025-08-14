// frontend/app/audiobook/page.tsx
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
    <main className="flex min-h-screen flex-col items-center p-12 bg-gray-900 text-white">
      <h1 className="text-4xl font-bold mb-8">PDF to Audiobook Converter</h1>
      <form onSubmit={handleSubmit} className="w-full max-w-lg bg-gray-800 p-8 rounded-lg">
        
        {/* File Upload */}
        <div className="mb-6">
          <label htmlFor="file" className="block mb-2 text-sm font-medium text-gray-300">
            Upload PDF
          </label>
          <input
            type="file"
            id="file"
            onChange={handleFileChange}
            accept=".pdf"
            className="bg-gray-700 border border-gray-600 text-white text-sm rounded-lg focus:ring-blue-500 focus:border-blue-500 block w-full p-2.5"
          />
        </div>

        {/* Voice Selection */}
        <div className="mb-6">
          <label htmlFor="voice" className="block mb-2 text-sm font-medium text-gray-300">
            Select Voice
          </label>
          <select
            id="voice"
            value={voice}
            onChange={(e) => setVoice(e.target.value)}
            className="bg-gray-700 border border-gray-600 text-white text-sm rounded-lg block w-full p-2.5"
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
          className="w-full text-white bg-blue-600 hover:bg-blue-700 focus:ring-4 focus:outline-none focus:ring-blue-800 font-medium rounded-lg text-sm px-5 py-2.5 text-center disabled:bg-gray-500"
        >
          {isLoading ? 'Converting...' : 'Convert to Audiobook'}
        </button>

        {/* Error Message */}
        {error && <p className="mt-4 text-red-500 text-center">{error}</p>}
      </form>
    </main>
  );
}
