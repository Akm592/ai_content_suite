'use client';

import { useRouter } from 'next/navigation';

interface PdfPreviewModalProps {
  sessionId: string;
  pdfUrl: string;
  onClose: () => void;
}

export default function PdfPreviewModal({ sessionId, pdfUrl, onClose }: PdfPreviewModalProps) {
  const router = useRouter();

  const handleFinalizeAndDownload = async () => {
    const link = document.createElement('a');
    link.href = pdfUrl;
    link.download = 'ai_storybook.pdf';
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);

    onClose();

    try {
      await fetch(`${process.env.NEXT_PUBLIC_API_URL}/storybook/session/${sessionId}/download`, {
        method: 'GET',
        keepalive: true,
      });
    } catch (error) {
      console.error("Cleanup request failed. Session will expire on its own.", error);
    }

    router.push('/');
  };

  return (
    <div className="fixed inset-0 bg-black/50 backdrop-blur-md flex justify-center items-center z-50 p-4">
      <div className="bg-gray-800 rounded-lg shadow-2xl max-w-4xl w-full h-[80vh] flex flex-col">
        
        {/* Header */}
        <div className="flex-shrink-0 flex justify-between items-center p-4 border-b border-gray-700">
          <h2 className="text-xl font-bold text-white">Storybook Preview</h2>
          <div>
            <button
              onClick={handleFinalizeAndDownload}
              className="bg-green-600 hover:bg-green-700 text-white font-bold py-2 px-4 rounded mr-4 transition-colors"
            >
              Finalize and Download
            </button>
            <button
              onClick={onClose}
              className="bg-gray-600 hover:bg-gray-700 text-white font-bold py-2 px-4 rounded transition-colors"
            >
              Close Preview
            </button>
          </div>
        </div>
        
        {/* Body */}
        <div className="flex-grow overflow-hidden">
          <embed
            src={pdfUrl}
            type="application/pdf"
            width="100%"
            height="100%"
          />
        </div>
      </div>
    </div>
  );
}
