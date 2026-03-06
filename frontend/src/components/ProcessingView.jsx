import React from 'react';
import { Loader2, CheckCircle, Video, X } from 'lucide-react';

export default function ProcessingView({ status, error, resultUrl, resetData }) {
  // statuses: 'idle', 'generating_script', 'generating_audio', 'processing_video', 'success', 'error'
  
  const steps = [
    { id: 'generating_script', label: 'Writing AI Script' },
    { id: 'generating_audio', label: 'Generating Professional Voiceover' },
    { id: 'processing_video', label: 'Assembling Final Video' }
  ];

  const getCurrentStepIndex = () => {
      if (status === 'success') return 3;
      if (status === 'error') return -1;
      return steps.findIndex(s => s.id === status);
  };

  const currentIndex = getCurrentStepIndex();

  if (status === 'idle') return null;

  return (
    <div className="bg-white rounded-xl border border-gray-200 p-8 shadow-sm w-full">
        {status === 'error' ? (
            <div className="text-center">
                <div className="w-16 h-16 bg-red-100 rounded-full flex items-center justify-center mx-auto mb-4">
                    <X className="w-8 h-8 text-red-500" />
                </div>
                <h3 className="text-xl font-bold text-gray-800 mb-2">Generation Failed</h3>
                <p className="text-red-500 mb-6">{error || 'An unexpected error occurred.'}</p>
                <button 
                  onClick={resetData}
                  className="px-6 py-2 bg-[var(--color-cobalt)] text-white rounded-lg font-medium hover:bg-blue-800 transition shadow-md"
                >
                    Try Again
                </button>
            </div>
        ) : status === 'success' ? (
            <div className="text-center">
                <div className="w-20 h-20 bg-[#98FF98] rounded-full flex items-center justify-center mx-auto mb-6 shadow-inner">
                    <CheckCircle className="w-10 h-10 text-emerald-800" />
                </div>
                <h3 className="text-2xl font-bold text-[#0047AB] mb-3">Your Video is Ready!</h3>
                <p className="text-gray-600 mb-8 max-w-md mx-auto">
                    The content has been automatically processed and sent securely to your n8n webhook for publishing.
                </p>
                
                {resultUrl && (
                    <div className="aspect-video w-full max-w-lg mx-auto bg-black rounded-xl overflow-hidden mb-8 shadow-lg">
                        <video controls className="w-full h-full object-contain">
                            <source src={resultUrl} type="video/mp4" />
                            Your browser does not support the video tag.
                        </video>
                    </div>
                )}
                
                <button 
                  onClick={resetData}
                  className="px-8 py-3 bg-[var(--color-cobalt)] text-white rounded-lg font-medium hover:bg-blue-800 transition shadow-md flex items-center justify-center mx-auto"
                >
                    <Video className="w-5 h-5 mr-2" />
                    Create Another Video
                </button>
            </div>
        ) : (
            <div>
                <h3 className="text-xl font-bold text-gray-800 mb-8 text-center">Processing Your Content</h3>
                
                <div className="space-y-6 max-w-md mx-auto relative before:absolute before:inset-0 before:ml-5 before:-translate-x-px md:before:mx-auto md:before:translate-x-0 before:h-full before:w-0.5 before:bg-gradient-to-b before:from-transparent before:via-gray-200 before:to-transparent">
                    {steps.map((step, idx) => {
                        const isCompleted = currentIndex > idx;
                        const isCurrent = currentIndex === idx;
                        
                        return (
                            <div key={step.id} className="relative flex items-center justify-between md:justify-normal md:odd:flex-row-reverse group is-active">
                                <div className={`flex items-center justify-center w-10 h-10 rounded-full border-4 shrink-0 md:order-1 md:group-odd:-translate-x-1/2 md:group-even:translate-x-1/2 shadow-sm ${
                                    isCompleted ? 'bg-[var(--color-mint)] border-white text-emerald-800' : 
                                    isCurrent ? 'bg-[var(--color-cobalt)] border-white text-white slide-up-animation' : 
                                    'bg-gray-100 border-white text-gray-400'
                                }`}>
                                    {isCompleted ? <CheckCircle className="w-5 h-5" /> : 
                                     isCurrent ? <Loader2 className="w-5 h-5 animate-spin" /> : 
                                     <span className="text-sm font-semibold">{idx + 1}</span>}
                                </div>
                                
                                <div className="w-[calc(100%-4rem)] md:w-[calc(50%-2.5rem)] bg-gray-50 p-4 rounded-xl border border-gray-100 shadow-sm ml-4 md:ml-0">
                                    <div className="flex items-center justify-between">
                                        <h4 className={`font-semibold ${isCurrent ? 'text-[var(--color-cobalt)]' : isCompleted ? 'text-gray-800' : 'text-gray-400'}`}>
                                            {step.label}
                                        </h4>
                                    </div>
                                    <p className="text-sm text-gray-500 mt-1">
                                        {isCompleted ? 'Completed successfully' : 
                                         isCurrent ? 'Working on it...' : 
                                         'Pending'}
                                    </p>
                                </div>
                            </div>
                        )
                    })}
                </div>
            </div>
        )}
    </div>
  );
}
