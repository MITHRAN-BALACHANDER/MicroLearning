import React, { useState } from 'react';
import { Upload, Video, Clock, CheckCircle, XCircle, Play, FileText, Tag } from 'lucide-react';
const UploadContent = () => {
  const [category, setCategory] = useState('');
  const [videoFile, setVideoFile] = useState(null);
  const [videoTitle, setVideoTitle] = useState('');
  const [uploading, setUploading] = useState(false);
  const [reviewVideos, setReviewVideos] = useState([]);

  const handleUpload = () => {
    if (!category || !videoFile || !videoTitle) return;

    setUploading(true);

    const nav=useNavigate();
    setTimeout(() => {
      const newVideo = {
        id: Date.now(),
        title: videoTitle,
        category,
        description: 'Auto-generated description based on video content analysis.',
        status: 'pending',
        uploadedAt: new Date().toLocaleString(),
      };
      setReviewVideos([...reviewVideos, newVideo]);
      setUploading(false);
      setCategory('');
      setVideoFile(null);
      setVideoTitle('');
    }, 2000);
  };

  const handleAccept = (id) => {
    setReviewVideos(reviewVideos.map(v => v.id === id ? { ...v, status: 'accepted' } : v));
  };

  const handleReject = (id) => {
    setReviewVideos(reviewVideos.map(v => v.id === id ? { ...v, status: 'rejected' } : v));
  };

  const getStatusColor = (status) => {
    switch (status) {
      case 'pending': return 'bg-yellow-100 text-yellow-800 border-yellow-200';
      case 'accepted': return 'bg-green-100 text-green-800 border-green-200';
      case 'rejected': return 'bg-red-100 text-red-800 border-red-200';
      default: return 'bg-gray-100 text-gray-800 border-gray-200';
    }
  };

  const getStatusIcon = (status) => {
    switch (status) {
      case 'pending': return <Clock className="w-4 h-4" />;
      case 'accepted': return <CheckCircle className="w-4 h-4" />;
      case 'rejected': return <XCircle className="w-4 h-4" />;
      default: return <Clock className="w-4 h-4" />;
    }
  };

  return (
    <div className="min-h-screen bg-gradient-to-br from-slate-50 to-blue-50 p-6">
      <div className="max-w-6xl mx-auto">
        {/* Header */}
        <div className="text-center mb-8">
          <h1 className="text-4xl font-bold text-gray-900 mb-2">Video Content Studio</h1>
          <p className="text-gray-600">Upload, review, and manage your video content</p>
        </div>

        {/* Upload Section */}
        <div className="bg-white rounded-2xl shadow-xl p-8 mb-8 border border-gray-100">
          <div className="flex items-center mb-6">
            <div className="bg-blue-100 p-3 rounded-full mr-4">
              <Upload className="w-6 h-6 text-blue-600" />
            </div>
            <h2 className="text-2xl font-semibold text-gray-900">Upload New Video</h2>
          </div>

          <div className="grid md:grid-cols-2 gap-6">
            <div className="space-y-4">
              <div>
                <label className="flex items-center text-sm font-medium text-gray-700 mb-2">
                  <FileText className="w-4 h-4 mr-2" />
                  Video Title
                </label>
                <input
                  type="text"
                  placeholder="Enter an engaging title for your video"
                  value={videoTitle}
                  onChange={(e) => setVideoTitle(e.target.value)}
                  className="w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent transition-all duration-200"
                />
              </div>

              <div>
                <label className="flex items-center text-sm font-medium text-gray-700 mb-2">
                  <Tag className="w-4 h-4 mr-2" />
                  Category
                </label>
                <input
                  type="text"
                  placeholder="e.g., Education, Entertainment, Tutorial"
                  value={category}
                  onChange={(e) => setCategory(e.target.value)}
                  className="w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent transition-all duration-200"
                />
              </div>
            </div>

            <div>
              <label className="flex items-center text-sm font-medium text-gray-700 mb-2">
                <Video className="w-4 h-4 mr-2" />
                Video File
              </label>
              <div className="border-2 border-dashed border-gray-300 rounded-lg p-6 text-center hover:border-blue-400 transition-colors duration-200">
                <input
                  type="file"
                  accept="video/*"
                  onChange={(e) => setVideoFile(e.target.files[0])}
                  className="hidden"
                  id="video-upload"
                />
                <label
                  htmlFor="video-upload"
                  className="cursor-pointer flex flex-col items-center"
                >
                  <Upload className="w-12 h-12 text-gray-400 mb-3" />
                  <span className="text-sm text-gray-600">
                    {videoFile ? videoFile.name : 'Click to upload video file'}
                  </span>
                  <span className="text-xs text-gray-400 mt-1">
                    MP4, MOV, AVI up to 100MB
                  </span>
                </label>
              </div>
            </div>
          </div>

          <div className="mt-6 flex justify-center">
            {uploading ? (
              <div className="flex items-center space-x-3 text-blue-600">
                <div className="animate-spin rounded-full h-5 w-5 border-b-2 border-blue-600"></div>
                <span className="font-medium">Processing video...</span>
              </div>
            ) : (
              <button
                onClick={handleUpload}
                disabled={!category || !videoFile || !videoTitle}
                className="bg-gradient-to-r from-blue-600 to-purple-600 text-white px-8 py-3 rounded-lg font-semibold hover:from-blue-700 hover:to-purple-700 disabled:opacity-50 disabled:cursor-not-allowed transition-all duration-200 transform hover:scale-105 shadow-lg"
              >
                Upload & Generate Content
              </button>
            )}
          </div>
        </div>

        {/* Review Section */}
        <div className="bg-white rounded-2xl shadow-xl p-8 border border-gray-100">
          <div className="flex items-center mb-6">
            <div className="bg-purple-100 p-3 rounded-full mr-4">
              <Play className="w-6 h-6 text-purple-600" />
            </div>
            <h3 className="text-2xl font-semibold text-gray-900">Content Review Queue</h3>
            <span className="ml-auto bg-gray-100 text-gray-700 px-3 py-1 rounded-full text-sm font-medium">
              {reviewVideos.length} videos
            </span>
          </div>

          {reviewVideos.length === 0 ? (
            <div className="text-center py-12">
              <Video className="w-16 h-16 text-gray-300 mx-auto mb-4" />
              <p className="text-gray-500 text-lg">No videos to review yet</p>
              <p className="text-gray-400 text-sm">Upload a video to get started</p>
            </div>
          ) : (
            <div className="space-y-4">
              {reviewVideos.map((video) => (
                <div
                  key={video.id}
                  className="border border-gray-200 rounded-xl p-6 hover:shadow-md transition-all duration-200 bg-gradient-to-r from-white to-gray-50"
                >
                  <div className="flex items-start justify-between">
                    <div className="flex-1">
                      <div className="flex items-center mb-2">
                        <h4 className="text-lg font-semibold text-gray-900 mr-3">{video.title}</h4>
                        <span className={`inline-flex items-center px-3 py-1 rounded-full text-xs font-medium border ${getStatusColor(video.status)}`}>
                          {getStatusIcon(video.status)}
                          <span className="ml-1 capitalize">{video.status}</span>
                        </span>
                      </div>
                      
                      <div className="flex items-center text-sm text-gray-600 mb-3 space-x-4">
                        <span className="flex items-center">
                          <Tag className="w-4 h-4 mr-1" />
                          {video.category}
                        </span>
                        <span className="flex items-center">
                          <Clock className="w-4 h-4 mr-1" />
                          {video.uploadedAt}
                        </span>
                      </div>
                      
                      <p className="text-gray-700 text-sm leading-relaxed">{video.description}</p>
                    </div>
                    
                    {video.status === 'pending' && (
                      <div className="flex space-x-2 ml-6">
                        <button
                          onClick={() => handleAccept(video.id)}
                          className="bg-green-500 hover:bg-green-600 text-white px-4 py-2 rounded-lg font-medium transition-colors duration-200 flex items-center space-x-1"
                        >
                          <CheckCircle className="w-4 h-4" />
                          <span>Accept</span>
                        </button>
                        <button
                          onClick={() => handleReject(video.id)}
                          className="bg-red-500 hover:bg-red-600 text-white px-4 py-2 rounded-lg font-medium transition-colors duration-200 flex items-center space-x-1"
                        >
                          <XCircle className="w-4 h-4" />
                          <span>Reject</span>
                        </button>
                      </div>
                    )}
                  </div>
                </div>
              ))}
            </div>
          )}
        </div>
      </div>
    </div>
  );
};

export default UploadContent;