import React, { useCallback, useState, useEffect } from 'react';
import { useDropzone } from 'react-dropzone';
import { UploadCloud, Image as ImageIcon, Video, X, CheckCircle } from 'lucide-react';

export default function MediaUploader({ onMediaReady }) {
  const [files, setFiles] = useState([]);
  const [mediaType, setMediaType] = useState(null); // 'video' | 'images' | null
  const [beforeName, setBeforeName] = useState(null);

  const onDrop = useCallback((acceptedFiles) => {
    if (acceptedFiles.length === 0) return;

    // Reject if mixed types or user already uploaded a video
    const hasVideo = acceptedFiles.some(f => f.type.startsWith('video/'));
    const hasImage = acceptedFiles.some(f => f.type.startsWith('image/'));
    
    if (hasVideo && hasImage) {
        alert("Please upload either one video or two images, not both.");
        return;
    }

    if (hasVideo) {
      if (acceptedFiles.length > 1) {
          alert("Please upload only one video.");
          return;
      }
      setFiles([acceptedFiles[0]]);
      setMediaType('video');
      return;
    }

    if (hasImage) {
      setFiles(prev => {
        const newFiles = [...prev, ...acceptedFiles].slice(0, 2);
        if (newFiles.length === 2 && !beforeName) {
            setBeforeName(newFiles[0].name);
        }
        setMediaType('images');
        return newFiles;
      });
    }
  }, [beforeName]);

  useEffect(() => {
    if (mediaType === 'video' && files.length === 1) {
      onMediaReady({ type: 'video', file: files[0] });
    } else if (mediaType === 'images' && files.length === 2 && beforeName) {
      const beforeFile = files.find(f => f.name === beforeName);
      const afterFile = files.find(f => f.name !== beforeName);
      onMediaReady({ type: 'images', before: beforeFile, after: afterFile });
    } else {
      onMediaReady(null);
    }
  }, [files, mediaType, beforeName, onMediaReady]);

  const { getRootProps, getInputProps, isDragActive } = useDropzone({
    onDrop,
    accept: {
      'image/*': ['.jpeg', '.jpg', '.png', '.webp'],
      'video/*': ['.mp4', '.mov', '.avi']
    },
    maxFiles: 2
  });

  const clearAll = (e) => {
      if (e) e.stopPropagation();
      setFiles([]);
      setMediaType(null);
      setBeforeName(null);
      onMediaReady(null);
  };

  const removeFile = (name, e) => {
      e.stopPropagation();
      setFiles(files.filter(f => f.name !== name));
      if (files.length === 1) {
          setMediaType(null);
      }
  };

  return (
    <div className="w-full">
      {files.length === 0 ? (
        <div 
          {...getRootProps()} 
          className={`border-2 border-dashed rounded-xl p-10 text-center cursor-pointer transition-all duration-300 ${
              isDragActive ? 'border-[var(--color-cobalt)] bg-blue-50' : 'border-gray-300 hover:border-[var(--color-cobalt)] bg-gray-50'
          }`}
        >
          <input {...getInputProps()} />
          <UploadCloud className="mx-auto h-12 w-12 text-gray-400 mb-4" />
          <h3 className="text-lg font-semibold text-gray-700">Drag & drop your files here</h3>
          <p className="text-sm text-gray-500 mt-2">Upload 1 Video OR 2 Photos ('Before' & 'After')</p>
          <p className="text-xs text-gray-400 mt-1">MP4, MOV, JPG, PNG up to 50MB</p>
        </div>
      ) : (
        <div className="bg-white rounded-xl border border-gray-200 p-6 shadow-sm">
          <div className="flex justify-between items-center mb-4">
              <h3 className="text-lg font-semibold text-[#0047AB]">
                  {mediaType === 'video' ? 'Video Uploaded' : 'Photos Uploaded'}
              </h3>
              <button onClick={clearAll} className="text-sm text-red-500 hover:text-red-700 flex items-center">
                  <X className="w-4 h-4 mr-1" /> Clear All
              </button>
          </div>

          {mediaType === 'video' && (
              <div className="flex items-center p-4 bg-blue-50 rounded-lg border border-blue-100">
                  <Video className="w-8 h-8 text-[var(--color-cobalt)] mr-4" />
                  <div className="flex-1 truncate">
                      <p className="font-medium text-gray-800 truncate">{files[0].name}</p>
                      <p className="text-xs text-gray-500">{(files[0].size / (1024*1024)).toFixed(2)} MB</p>
                  </div>
                  <CheckCircle className="w-6 h-6 text-[var(--color-mint)]" />
              </div>
          )}

          {mediaType === 'images' && (
              <div className="space-y-4">
                  {files.length === 1 && (
                      <div 
                        {...getRootProps()} 
                        className="border-2 border-dashed border-gray-300 rounded-lg p-6 text-center cursor-pointer hover:border-[var(--color-cobalt)] hover:bg-gray-50 transition-colors"
                      >
                         <input {...getInputProps()} />
                         <p className="text-gray-600 font-medium">+ Add second photo</p>
                      </div>
                  )}
                  
                  <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                      {files.map((file, idx) => (
                          <div 
                              key={file.name} 
                              className={`relative rounded-lg overflow-hidden border-2 transition-all ${beforeName === file.name ? 'border-[var(--color-cobalt)] shadow-md' : 'border-gray-200'}`}
                          >
                              <div className="absolute top-2 right-2 flex space-x-2 z-10">
                                  <button onClick={(e) => removeFile(file.name, e)} className="bg-white/80 backdrop-blur rounded-full p-1 text-gray-700 hover:text-red-500 hover:bg-white shadow">
                                      <X className="w-4 h-4" />
                                  </button>
                              </div>
                              <div className="h-40 bg-gray-100 flex items-center justify-center overflow-hidden">
                                  <img 
                                      src={URL.createObjectURL(file)} 
                                      alt="upload preview" 
                                      className="object-cover w-full h-full opacity-90"
                                  />
                              </div>
                              <div className="p-3 bg-white flex justify-between items-center">
                                  <p className="text-sm truncate w-1/2 font-medium text-gray-700">{file.name}</p>
                                  <div className="flex space-x-2">
                                      <button 
                                          onClick={() => setBeforeName(file.name)}
                                          className={`px-3 py-1 text-xs rounded-full font-medium transition-colors ${beforeName === file.name ? 'bg-[var(--color-cobalt)] text-white' : 'bg-gray-100 text-gray-600 hover:bg-gray-200'}`}
                                      >
                                          Before
                                      </button>
                                      <button 
                                          onClick={() => setBeforeName(files.find(f => f.name !== file.name)?.name || null)}
                                          className={`px-3 py-1 text-xs rounded-full font-medium transition-colors ${beforeName !== file.name && beforeName !== null ? 'bg-[var(--color-mint)] text-slate-800' : 'bg-gray-100 text-gray-600 hover:bg-gray-200'}`}
                                      >
                                          After
                                      </button>
                                  </div>
                              </div>
                          </div>
                      ))}
                  </div>
                  {files.length === 2 && !beforeName && (
                      <p className="text-sm text-red-500 font-medium">Please select which photo is "Before" and "After".</p>
                  )}
                  {files.length === 2 && beforeName && (
                      <div className="flex items-center justify-center text-sm text-[var(--color-cobalt)] font-medium bg-blue-50 py-2 rounded-md">
                          <CheckCircle className="w-4 h-4 mr-2" /> Photos ready for processing
                      </div>
                  )}
              </div>
          )}
        </div>
      )}
    </div>
  );
}
