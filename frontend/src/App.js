import React, { useState, useEffect } from 'react';
import './App.css';

function App() {
  const [prompt, setPrompt] = useState('');
  const [loading, setLoading] = useState(false);
  const [generatedImage, setGeneratedImage] = useState(null);
  const [imageHistory, setImageHistory] = useState([]);
  const [error, setError] = useState('');
  const [fullscreenImage, setFullscreenImage] = useState(null);

  const backendUrl = process.env.REACT_APP_BACKEND_URL || 'http://localhost:8001';

  useEffect(() => {
    fetchImageHistory();
  }, []);

  const fetchImageHistory = async () => {
    try {
      const response = await fetch(`${backendUrl}/api/images?limit=6`);
      if (response.ok) {
        const images = await response.json();
        setImageHistory(images);
      }
    } catch (err) {
      console.error('Error fetching image history:', err);
    }
  };

  const generateImage = async () => {
    if (!prompt.trim()) {
      setError('Please enter a prompt');
      return;
    }

    setLoading(true);
    setError('');
    setGeneratedImage(null);

    try {
      const response = await fetch(`${backendUrl}/api/generate-image`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({ prompt: prompt.trim() }),
      });

      if (!response.ok) {
        const errorData = await response.json();
        throw new Error(errorData.detail || 'Failed to generate image');
      }

      const result = await response.json();
      setGeneratedImage(result);
      setPrompt('');
      
      // Refresh history
      await fetchImageHistory();
      
    } catch (err) {
      setError(err.message || 'Failed to generate image');
    } finally {
      setLoading(false);
    }
  };

  const handleKeyPress = (e) => {
    if (e.key === 'Enter' && !loading) {
      generateImage();
    }
  };

  const openFullscreen = (image) => {
    setFullscreenImage(image);
  };

  const closeFullscreen = () => {
    setFullscreenImage(null);
  };

  const handleFullscreenKeyPress = (e) => {
    if (e.key === 'Escape') {
      closeFullscreen();
    }
  };

  const deleteImage = async (imageId) => {
    try {
      const response = await fetch(`${backendUrl}/api/images/${imageId}`, {
        method: 'DELETE',
      });
      
      if (response.ok) {
        setImageHistory(prev => prev.filter(img => img.id !== imageId));
        if (generatedImage && generatedImage.id === imageId) {
          setGeneratedImage(null);
        }
      }
    } catch (err) {
      console.error('Error deleting image:', err);
    }
  };

  return (
    <div className="min-h-screen bg-gradient-to-br from-purple-900 via-blue-900 to-indigo-900">
      {/* Header */}
      <div className="bg-black/20 backdrop-blur-sm border-b border-white/10">
        <div className="max-w-6xl mx-auto px-6 py-4">
          <div className="flex items-center space-x-3">
            <div className="w-10 h-10 bg-gradient-to-r from-yellow-400 to-orange-500 rounded-full flex items-center justify-center">
              <span className="text-xl">🍌</span>
            </div>
            <div>
              <h1 className="text-2xl font-bold text-white">Nano Banana</h1>
              <p className="text-blue-200 text-sm">AI Image Generator</p>
            </div>
          </div>
        </div>
      </div>

      <div className="max-w-6xl mx-auto px-6 py-8">
        {/* Input Section */}
        <div className="bg-white/10 backdrop-blur-md rounded-2xl border border-white/20 p-8 mb-8">
          <div className="text-center mb-6">
            <h2 className="text-3xl font-bold text-white mb-2">Create Amazing Images</h2>
            <p className="text-blue-200">Powered by Gemini's Nano Banana Model</p>
          </div>

          <div className="max-w-2xl mx-auto">
            <div className="relative">
              <input
                type="text"
                value={prompt}
                onChange={(e) => setPrompt(e.target.value)}
                onKeyPress={handleKeyPress}
                placeholder="Describe the image you want to create..."
                className="w-full px-6 py-4 bg-white/10 border border-white/20 rounded-xl text-white placeholder-blue-200 focus:outline-none focus:ring-2 focus:ring-yellow-400 focus:border-transparent transition-all duration-200"
                disabled={loading}
              />
              <button
                onClick={generateImage}
                disabled={loading || !prompt.trim()}
                className="absolute right-2 top-2 bottom-2 px-6 bg-gradient-to-r from-yellow-400 to-orange-500 text-white font-semibold rounded-lg hover:from-yellow-500 hover:to-orange-600 disabled:opacity-50 disabled:cursor-not-allowed transition-all duration-200 flex items-center space-x-2"
              >
                {loading ? (
                  <>
                    <div className="w-4 h-4 border-2 border-white border-t-transparent rounded-full animate-spin"></div>
                    <span>Generating...</span>
                  </>
                ) : (
                  <>
                    <span>Generate</span>
                    <span>✨</span>
                  </>
                )}
              </button>
            </div>

            {error && (
              <div className="mt-4 p-4 bg-red-500/20 border border-red-500/30 rounded-lg text-red-200">
                {error}
              </div>
            )}
          </div>
        </div>

        {/* Generated Image */}
        {generatedImage && (
          <div className="bg-white/10 backdrop-blur-md rounded-2xl border border-white/20 p-8 mb-8">
            <h3 className="text-xl font-bold text-white mb-4">Latest Creation</h3>
            <div className="grid md:grid-cols-2 gap-6">
              <div className="relative group">
                <img
                  src={generatedImage.image_url}
                  alt={generatedImage.prompt}
                  className="w-full h-64 object-cover rounded-xl border border-white/20 cursor-pointer hover:opacity-90 transition-opacity duration-200"
                  onClick={() => openFullscreen(generatedImage)}
                />
                <button
                  onClick={() => deleteImage(generatedImage.id)}
                  className="absolute top-2 right-2 w-8 h-8 bg-red-500/80 hover:bg-red-500 rounded-full flex items-center justify-center text-white opacity-0 group-hover:opacity-100 transition-opacity duration-200"
                >
                  ×
                </button>
              </div>
              <div className="flex flex-col justify-center">
                <h4 className="text-lg font-semibold text-white mb-2">Prompt:</h4>
                <p className="text-blue-200 bg-black/20 rounded-lg p-4 border border-white/10">
                  {generatedImage.prompt}
                </p>
                <div className="mt-4 text-sm text-blue-300">
                  Created: {new Date(generatedImage.created_at).toLocaleString()}
                </div>
              </div>
            </div>
          </div>
        )}

        {/* Image History */}
        {imageHistory.length > 0 && (
          <div className="bg-white/10 backdrop-blur-md rounded-2xl border border-white/20 p-8">
            <h3 className="text-xl font-bold text-white mb-6">Recent Creations</h3>
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
              {imageHistory.map((image) => (
                <div key={image.id} className="relative group">
                  <div className="bg-white/5 rounded-xl p-4 border border-white/10 hover:border-white/20 transition-all duration-200">
                    <img
                      src={image.image_url}
                      alt={image.prompt}
                      className="w-full h-40 object-cover rounded-lg mb-3 cursor-pointer hover:opacity-90 transition-opacity duration-200"
                      onClick={() => openFullscreen(image)}
                    />
                    <p className="text-blue-200 text-sm line-clamp-2 mb-2">
                      {image.prompt}
                    </p>
                    <div className="text-xs text-blue-300">
                      {new Date(image.created_at).toLocaleDateString()}
                    </div>
                    <button
                      onClick={() => deleteImage(image.id)}
                      className="absolute top-2 right-2 w-6 h-6 bg-red-500/80 hover:bg-red-500 rounded-full flex items-center justify-center text-white text-sm opacity-0 group-hover:opacity-100 transition-opacity duration-200"
                    >
                      ×
                    </button>
                  </div>
                </div>
              ))}
            </div>
          </div>
        )}

        {/* Empty State */}
        {imageHistory.length === 0 && !generatedImage && !loading && (
          <div className="text-center py-12">
            <div className="text-6xl mb-4">🎨</div>
            <h3 className="text-xl font-bold text-white mb-2">No images yet</h3>
            <p className="text-blue-200">Start by entering a prompt above to create your first image!</p>
          </div>
        )}
      </div>

      {/* Fullscreen Modal */}
      {fullscreenImage && (
        <div 
          className="fixed inset-0 bg-black/90 backdrop-blur-sm z-50 flex items-center justify-center p-4"
          onClick={closeFullscreen}
          onKeyDown={handleFullscreenKeyPress}
          tabIndex={0}
        >
          <div className="relative w-full h-full max-w-7xl max-h-full flex flex-col">
            {/* Close button */}
            <button
              onClick={closeFullscreen}
              className="absolute top-4 right-4 z-10 w-10 h-10 bg-black/50 hover:bg-black/70 rounded-full flex items-center justify-center text-white text-xl transition-colors duration-200"
            >
              ×
            </button>
            
            {/* Image container */}
            <div className="flex-1 flex items-center justify-center min-h-0 p-6">
              <img
                src={fullscreenImage.image_url}
                alt={fullscreenImage.prompt}
                className="max-w-full max-h-full w-auto h-auto object-contain rounded-lg shadow-2xl"
                onClick={(e) => e.stopPropagation()}
                style={{ 
                  maxWidth: 'calc(100vw - 3rem)', 
                  maxHeight: 'calc(100vh - 10rem)' 
                }}
              />
            </div>
            
            {/* Image info */}
            <div className="bg-black/50 backdrop-blur-sm rounded-lg p-4 mx-4 mb-4 flex-shrink-0">
              <h3 className="text-white font-semibold mb-2">Prompt:</h3>
              <p className="text-blue-200 mb-2">{fullscreenImage.prompt}</p>
              <p className="text-blue-300 text-sm">
                Created: {new Date(fullscreenImage.created_at).toLocaleString()}
              </p>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}

export default App;