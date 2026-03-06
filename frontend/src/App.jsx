import React, { useState } from 'react';
import MediaUploader from './components/MediaUploader';
import ProcessingView from './components/ProcessingView';
import { Activity, Stethoscope } from 'lucide-react';
import axios from 'axios';

function App() {
  const [mediaData, setMediaData] = useState(null);
  const [description, setDescription] = useState('');
  const [status, setStatus] = useState('idle'); // idle, generating_script, generating_audio, processing_video, success, error
  const [errorDetails, setErrorDetails] = useState('');
  const [resultVideo, setResultVideo] = useState(null);

  const isFormValid = mediaData !== null && description.trim().length > 10;

  const handleSubmit = async (e) => {
    e.preventDefault();
    if (!isFormValid) return;

    setStatus('generating_script');
    
    // Create FormData mapping files
    const formData = new FormData();
    formData.append('description', description);
    formData.append('media_type', mediaData.type);
    
    if (mediaData.type === 'video') {
       formData.append('video_file', mediaData.file);
    } else {
       formData.append('before_image', mediaData.before);
       formData.append('after_image', mediaData.after);
    }

    try {
        // Backend currently mapped to http://localhost:8000 via docker-compose usually, but via Vite proxy or direct fetch is fine.
        // For development we will point to localhost:8000 dynamically or env variable.
        const apiUrl = import.meta.env.VITE_API_URL || 'http://localhost:8000';
        
        // Mock processing steps just for visual transition before the real API handles it all. 
        // In reality, the API will be a long polling or websocket connection, 
        // but for now we will simulate the steps changing while we wait for the single POST request if we don't have Server Sent Events setup yet.

        // Start dummy timer to advance UI visually
        const stepTimer1 = setTimeout(() => setStatus('generating_audio'), 3000);
        const stepTimer2 = setTimeout(() => setStatus('processing_video'), 7000);

        // Actual API Call
        const response = await axios.post(`${apiUrl}/api/generate`, formData, {
            headers: { 'Content-Type': 'multipart/form-data' }
        });

        clearTimeout(stepTimer1);
        clearTimeout(stepTimer2);
        
        setStatus('success');
        setResultVideo(response.data.video_url || null);

    } catch (err) {
        console.error("Error during generation", err);
        setErrorDetails(err.response?.data?.detail || "Failed to contact server.");
        setStatus('error');
    }
  };

  const resetAll = () => {
      setMediaData(null);
      setDescription('');
      setStatus('idle');
      setErrorDetails('');
      setResultVideo(null);
  }

  return (
    <div className="min-h-screen bg-[#f8fafc] font-sans selection:bg-[#98FF98] selection:text-slate-800">
      {/* Header */}
      <header className="bg-white border-b border-gray-200 shadow-sm sticky top-0 z-10">
        <div className="max-w-5xl mx-auto px-6 h-16 flex items-center justify-between">
          <div className="flex items-center space-x-2">
            <div className="bg-[#0047AB] p-2 rounded-lg text-white">
              <Stethoscope className="w-5 h-5" />
            </div>
            <h1 className="text-xl font-bold tracking-tight text-[#0047AB]">Dental<span className="text-emerald-500 font-extrabold">Flow</span></h1>
          </div>
          <div className="text-sm font-medium text-gray-500 flex items-center">
            <Activity className="w-4 h-4 mr-2 text-[#98FF98]" />
            AI Content Automator
          </div>
        </div>
      </header>

      {/* Main Content */}
      <main className="max-w-4xl mx-auto px-6 py-12">
        <div className="text-center mb-10">
          <h2 className="text-3xl font-extrabold text-gray-900 mb-4">Create Professional Clinic Content Instantly</h2>
          <p className="text-gray-600 max-w-2xl mx-auto text-lg">
            Upload your clinical media (Before/After photos or video), provide a quick technical description, and let our AI handle the script, voiceover, and video editing.
          </p>
        </div>

        {status === 'idle' ? (
            <div className="grid grid-cols-1 lg:grid-cols-2 gap-8">
              {/* Left Column - Uploader */}
              <div className="space-y-6">
                <div className="bg-white p-1 rounded-xl shadow-sm border border-gray-100">
                  <MediaUploader onMediaReady={setMediaData} />
                </div>
              </div>

              {/* Right Column - Form */}
              <div className="bg-white rounded-xl shadow-sm border border-gray-100 p-8">
                <h3 className="text-lg font-semibold text-gray-800 mb-4 flex items-center">
                   Technical Details
                   <span className="ml-2 px-2 py-0.5 rounded text-[10px] font-bold uppercase tracking-wider bg-blue-100 text-[#0047AB]">Required</span>
                </h3>
                
                <form onSubmit={handleSubmit} className="space-y-6 flex flex-col h-[calc(100%-3rem)]">
                  <div className="flex-1">
                    <label htmlFor="description" className="block text-sm font-medium text-gray-700 mb-2">
                      Clinical Description & Observations
                    </label>
                    <textarea 
                      id="description"
                      value={description}
                      onChange={(e) => setDescription(e.target.value)}
                      placeholder="e.g. Patient presented with a fractured upper central incisor. Applied composite resin restoration matching shade A2..."
                      className="w-full h-40 rounded-lg border-gray-300 shadow-sm focus:border-[#0047AB] focus:ring focus:ring-blue-200 focus:ring-opacity-50 resize-none transition-shadow p-3 border"
                    />
                    <p className="text-xs text-gray-500 mt-2">
                        Be specific with medical terms; the AI will transcribe this into an engaging Reel script for your audience.
                    </p>
                  </div>

                  <div className="pt-4 border-t border-gray-100">
                    <button
                      type="submit"
                      disabled={!isFormValid}
                      className={`w-full py-3 px-4 rounded-xl font-bold flex items-center justify-center transition-all ${
                          isFormValid 
                          ? 'bg-[#0047AB] text-white hover:bg-blue-800 shadow-lg hover:shadow-xl transform hover:-translate-y-0.5' 
                          : 'bg-gray-100 text-gray-400 cursor-not-allowed'
                      }`}
                    >
                      Generate Video Now
                    </button>
                    {!mediaData && (
                        <p className="text-xs text-center text-red-400 mt-3 font-medium">Please upload media to continue.</p>
                    )}
                  </div>
                </form>
              </div>
            </div>
        ) : (
            <div className="max-w-2xl mx-auto flex justify-center">
                <ProcessingView 
                    status={status} 
                    error={errorDetails} 
                    resultUrl={resultVideo} 
                    resetData={resetAll} 
                />
            </div>
        )}
      </main>
    </div>
  );
}

export default App;
