import React, { useState } from 'react';
import MediaUploader from './components/MediaUploader';
import ProcessingView from './components/ProcessingView';
import { Activity, Stethoscope, Edit3, Video, Volume2, Instagram, Send } from 'lucide-react';
import axios from 'axios';

function App() {
  const [mediaData, setMediaData] = useState(null);
  const [description, setDescription] = useState('');
  const [status, setStatus] = useState('idle'); // idle, generating_script, reviewing_script, generating_audio, processing_video, success, error
  const [errorDetails, setErrorDetails] = useState('');
  const [resultVideo, setResultVideo] = useState(null);
  const [scriptData, setScriptData] = useState(null);
  const [editableScript, setEditableScript] = useState('');
  const [editableCopy, setEditableCopy] = useState('');

  const isFormValid = mediaData !== null && description.trim().length > 10;

  const handleGenerateScript = async (e) => {
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
        const apiUrl = import.meta.env.VITE_API_URL || 'http://localhost:8000';
        
        const response = await axios.post(`${apiUrl}/api/generate-script`, formData, {
            headers: { 'Content-Type': 'multipart/form-data' }
        });

        setScriptData({
            session_id: response.data.session_id,
            media_type: response.data.media_type,
            vid_path: response.data.vid_path,
            before_path: response.data.before_path,
            after_path: response.data.after_path
        });
        setEditableScript(response.data.script);
        setStatus('reviewing_script');

    } catch (err) {
        console.error("Error generating script", err);
        setErrorDetails(err.response?.data?.detail || "Failed to contact server.");
        setStatus('error');
    }
  };

  const handleCreatePreview = async () => {
    setStatus('generating_preview');
    
    const formData = new FormData();
    formData.append('script_text', editableScript);
    formData.append('media_type', scriptData.media_type);
    formData.append('vid_path', scriptData.vid_path || '');
    formData.append('before_path', scriptData.before_path || '');
    formData.append('after_path', scriptData.after_path || '');

    try {
        const apiUrl = import.meta.env.VITE_API_URL || 'http://localhost:8000';
        const response = await axios.post(`${apiUrl}/api/preview-video`, formData);
        
        setScriptData(prev => ({
            ...prev,
            preview_path: response.data.preview_path,
            preview_url: response.data.preview_url
        }));
        setStatus('reviewing_preview');
    } catch (err) {
        setErrorDetails(err.response?.data?.detail || "Failed to contact server.");
        setStatus('error');
    }
  };

  const handleFinalizeVideo = async () => {
    setStatus('generating_final');
    
    const formData = new FormData();
    formData.append('script_text', editableScript);
    formData.append('preview_path', scriptData.preview_path);

    try {
        const apiUrl = import.meta.env.VITE_API_URL || 'http://localhost:8000';
        const response = await axios.post(`${apiUrl}/api/finalize-video`, formData);
        
        setScriptData(prev => ({
            ...prev,
            final_video_path: response.data.final_video_path,
            final_video_url: response.data.final_video_url,
            audio_path: response.data.audio_path
        }));
        setStatus('reviewing_final');
    } catch (err) {
        setErrorDetails(err.response?.data?.detail || "Failed to contact server.");
        setStatus('error');
    }
  };

  const handleGenerateCopy = async () => {
    setStatus('generating_copy');
    const formData = new FormData();
    formData.append('description', description);
    formData.append('script_text', editableScript);

    try {
        const apiUrl = import.meta.env.VITE_API_URL || 'http://localhost:8000';
        const response = await axios.post(`${apiUrl}/api/generate-instagram-copy`, formData);
        
        setEditableCopy(response.data.copy);
        setStatus('reviewing_copy');
    } catch (err) {
        setErrorDetails(err.response?.data?.detail || "Failed to contact server.");
        setStatus('error');
    }
  };

  const handlePublish = async () => {
    setStatus('publishing');
    const formData = new FormData();
    formData.append('description', description);
    formData.append('script_text', editableScript);
    formData.append('copy_text', editableCopy);
    formData.append('final_video_path', scriptData.final_video_path);
    formData.append('audio_path', scriptData.audio_path || '');
    formData.append('vid_path', scriptData.vid_path || '');
    formData.append('before_path', scriptData.before_path || '');
    formData.append('after_path', scriptData.after_path || '');
    formData.append('preview_path', scriptData.preview_path || '');

    try {
        const apiUrl = import.meta.env.VITE_API_URL || 'http://localhost:8000';
        await axios.post(`${apiUrl}/api/publish`, formData);
        
        setStatus('success');
    } catch (err) {
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
      setScriptData(null);
      setEditableScript('');
      setEditableCopy('');
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
                
                <form onSubmit={handleGenerateScript} className="space-y-6 flex flex-col h-[calc(100%-3rem)]">
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
                      Generar Guion
                    </button>
                    {!mediaData && (
                        <p className="text-xs text-center text-red-400 mt-3 font-medium">Please upload media to continue.</p>
                    )}
                  </div>
                </form>
              </div>
            </div>
        ) : status === 'reviewing_script' ? (
            <div className="max-w-2xl mx-auto bg-white rounded-xl shadow-sm border border-gray-100 p-8">
                <div className="flex items-center space-x-3 mb-6">
                    <div className="bg-blue-100 p-2 rounded-lg text-[#0047AB]">
                        <Edit3 className="w-6 h-6" />
                    </div>
                    <h3 className="text-2xl font-bold text-gray-800">Revisa tu Guion</h3>
                </div>
                <p className="text-gray-600 mb-6">Hemos generado el siguiente guion en español de Chile. Puedes editarlo antes de generar el video final.</p>
                <textarea
                    value={editableScript}
                    onChange={(e) => setEditableScript(e.target.value)}
                    className="w-full h-48 rounded-lg border-gray-300 shadow-sm focus:border-[#0047AB] focus:ring focus:ring-blue-200 resize-none p-4 text-gray-700 text-lg leading-relaxed mb-6 border"
                />
                <div className="flex space-x-4">
                    <button onClick={() => setStatus('idle')} className="px-6 py-3 rounded-xl font-bold text-gray-600 bg-gray-100 hover:bg-gray-200 transition-all">
                        Atrás
                    </button>
                    <button onClick={handleCreatePreview} className="flex-1 py-3 px-4 rounded-xl font-bold flex items-center justify-center text-white bg-[#0047AB] hover:bg-blue-800 shadow-lg hover:shadow-xl transition-all">
                        <Video className="w-5 h-5 mr-2" />
                        Generar Video Visual (Gratis)
                    </button>
                </div>
            </div>
        ) : status === 'reviewing_preview' ? (
            <div className="max-w-2xl mx-auto bg-white rounded-xl shadow-sm border border-gray-100 p-8">
                <div className="flex items-center space-x-3 mb-6">
                    <div className="bg-blue-100 p-2 rounded-lg text-[#0047AB]">
                        <Video className="w-6 h-6" />
                    </div>
                    <h3 className="text-2xl font-bold text-gray-800">Previsualización Visual</h3>
                </div>
                <p className="text-gray-600 mb-6">Video mudo con música de fondo. Revisa los tiempos y subtítulos antes de gastar saldo en ElevenLabs.</p>
                <div className="aspect-video w-full bg-black rounded-xl overflow-hidden mb-6 shadow-md">
                    <video controls src={scriptData?.preview_url} className="w-full h-full object-contain"></video>
                </div>
                <div className="flex space-x-4">
                    <button onClick={() => setStatus('reviewing_script')} className="px-6 py-3 rounded-xl font-bold text-gray-600 bg-gray-100 hover:bg-gray-200 transition-all">
                        Editar Guion
                    </button>
                    <button onClick={handleFinalizeVideo} className="flex-1 py-3 px-4 rounded-xl font-bold flex items-center justify-center text-white bg-emerald-600 hover:bg-emerald-700 shadow-lg hover:shadow-xl transition-all">
                        <Volume2 className="w-5 h-5 mr-2" />
                        Añadir Voz (ElevenLabs)
                    </button>
                </div>
            </div>
        ) : status === 'reviewing_final' ? (
            <div className="max-w-2xl mx-auto bg-white rounded-xl shadow-sm border border-gray-100 p-8">
                <div className="flex items-center space-x-3 mb-6">
                    <div className="bg-emerald-100 p-2 rounded-lg text-emerald-700">
                        <Volume2 className="w-6 h-6" />
                    </div>
                    <h3 className="text-2xl font-bold text-gray-800">Video Finalizado</h3>
                </div>
                <p className="text-gray-600 mb-6">Video completo con voz profesional. Listo para generar el texto de Instagram.</p>
                <div className="aspect-video w-full bg-black rounded-xl overflow-hidden mb-6 shadow-md">
                    <video controls src={scriptData?.final_video_url} className="w-full h-full object-contain"></video>
                </div>
                <button onClick={handleGenerateCopy} className="w-full py-3 px-4 rounded-xl font-bold flex items-center justify-center text-white bg-[#0047AB] hover:bg-blue-800 shadow-lg hover:shadow-xl transition-all">
                    <Instagram className="w-5 h-5 mr-2" />
                    Generar Copy para Instagram
                </button>
            </div>
        ) : status === 'reviewing_copy' ? (
            <div className="max-md:px-2 max-w-xl mx-auto">
                <div className="bg-white rounded-xl shadow-md border border-gray-200 overflow-hidden">
                    <div className="p-4 border-b border-gray-100 flex items-center space-x-3">
                        <div className="w-8 h-8 rounded-full bg-gradient-to-tr from-yellow-400 via-pink-500 to-purple-500 p-0.5">
                            <div className="bg-white w-full h-full rounded-full border-2 border-white flex items-center justify-center overflow-hidden">
                                <Stethoscope className="w-4 h-4 text-gray-700" />
                            </div>
                        </div>
                        <span className="font-semibold text-sm">dentalflow_clinic</span>
                    </div>
                    <div className="aspect-square bg-black w-full relative">
                        <video controls src={scriptData?.final_video_url} className="w-full h-full object-contain bg-black"></video>
                    </div>
                    <div className="p-4">
                        <textarea
                            value={editableCopy}
                            onChange={(e) => setEditableCopy(e.target.value)}
                            className="w-full h-56 rounded-lg border border-transparent hover:border-gray-200 focus:border-gray-300 focus:ring-0 resize-none text-sm text-gray-800 p-2 transition-all bg-gray-50"
                        />
                    </div>
                    <div className="p-4 pt-0">
                        <button onClick={handlePublish} className="w-full py-3 px-4 rounded-xl font-bold flex items-center justify-center text-white bg-gradient-to-r from-purple-600 to-pink-600 hover:from-purple-700 hover:to-pink-700 shadow-lg transition-all">
                            <Send className="w-5 h-5 mr-2" />
                            Publicar a n8n
                        </button>
                    </div>
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
