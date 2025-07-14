import React, { useState } from 'react';

const UploadContent = () => {
  const [category, setCategory] = useState('');
  const [videoFile, setVideoFile] = useState(null);
  const [videoTitle, setVideoTitle] = useState('');
  const [uploading, setUploading] = useState(false);
  const [reviewVideos, setReviewVideos] = useState([]);

  const handleUpload = () => {
    if (!category || !videoFile || !videoTitle) return;

    setUploading(true);

    // Simulate video generation delay
    setTimeout(() => {
      const newVideo = {
        id: Date.now(),
        title: videoTitle,
        category,
        description: 'Auto-generated description placeholder.',
        status: 'pending',
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

  return (
    <div className="p-6 m-9">
      <h2 className="text-2xl font-semibold mb-4">Upload Video Content</h2>

      <div className="flex flex-col gap-4 max-w-xl">
        <input
          type="text"
          placeholder="Enter Video Title"
          value={videoTitle}
          onChange={(e) => setVideoTitle(e.target.value)}
          className="border rounded p-2"
        />
        <input
          type="text"
          placeholder="Enter Category"
          value={category}
          onChange={(e) => setCategory(e.target.value)}
          className="border rounded p-2"
        />
        <input
          type="file"
          accept="video/*"
          onChange={(e) => setVideoFile(e.target.files[0])}
          className="border rounded p-2"
        />

        {uploading ? (
          <div className="text-blue-500 font-medium">Video generation in progress...</div>
        ) : (
          <button
            onClick={handleUpload}
            className="bg-green-600 text-white px-4 py-2 rounded w-fit"
          >
            Upload File
          </button>
        )}
      </div>

      <h3 className="text-xl font-semibold mt-8 mb-3">Videos to be Reviewed</h3>
      <div className="flex flex-col gap-4">
        {reviewVideos.map((video) => (
          <div
            key={video.id}
            className="flex items-start justify-between p-4 rounded-lg border shadow"
          >
            <div>
              <h4 className="font-bold">{video.title}</h4>
              <p className="text-sm text-gray-600">Category: {video.category}</p>
              <p className="text-sm">{video.description}</p>
            </div>
            <div className="flex flex-col gap-2">
              <button
                onClick={() => handleAccept(video.id)}
                className="bg-green-500 text-white px-3 py-1 rounded"
              >
                Accept
              </button>
              <button
                onClick={() => handleReject(video.id)}
                className="bg-red-500 text-white px-3 py-1 rounded"
              >
                Reject
              </button>
            </div>
          </div>
        ))}
      </div>
    </div>
  );
};

export default UploadContent;
