const Video = require('../models/Video');
const Rating = require('../models/Rating');
const fs = require('fs');
const path = require('path');
const { getWithCache, delWithCache } = require('../redis/cacheHelper');

// GET: All videos by category
exports.getVideosByCategory = async (req, res) => {
  const categoryId = req.params.categoryId;
  const cacheKey = `videos:category:${categoryId}`;

  try {
    const videos = await getWithCache(cacheKey, () => Video.find({ categoryId }));
    if (!videos.length) return res.status(404).json({ message: 'No videos found for this category' });
    res.json(videos);
  } catch (error) {
    res.status(500).json({ message: 'Error fetching videos by category', error: error.message });
  }
};

// GET: All videos
exports.getAllVideos = async (req, res) => {
  const cacheKey = 'videos:all';

  try {
    const videos = await getWithCache(cacheKey, () => Video.find());
    if (!videos.length) return res.status(404).json({ message: 'No videos found' });
    res.json(videos);
  } catch (error) {
    res.status(500).json({ message: 'Error fetching videos', error: error.message });
  }
};

// GET: Search videos (with optional cache)
exports.searchVideos = async (req, res) => {
  const { query } = req.query;
  const cacheKey = `videos:search:${query}`;

  try {
    const videos = await getWithCache(cacheKey, () => 
      Video.find({ title: { $regex: query, $options: 'i' } }),
      300 // optional: cache search results for 5 min
    );
    res.json(videos);
  } catch (error) {
    res.status(500).json({ message: 'Error searching videos', error: error.message });
  }
};

// POST: Create new video
exports.createVideo = async (req, res) => {
  try {
    const { title, description, thumbnailUrl, categoryId } = req.body;
    const videoUrl = `/uploads/${req.file.filename}`;

    const newVideo = new Video({
      title,
      description,
      videoUrl,
      thumbnailUrl,
      categoryId,
      uploadedBy: req.user.id,
      views: 0,
      averageRating: 0,
      ratingsCount: 0,
      isPublished: true,
      tags: []
    });

    await newVideo.save();

    // Invalidate related caches
    await delWithCache('videos:all');
    await delWithCache(`videos:category:${categoryId}`);

    res.status(201).json(newVideo);
  } catch (error) {
    res.status(500).json({ message: 'Error creating video', error: error.message });
  }
};

// PUT: Update video
exports.updateVideo = async (req, res) => {
  const videoId = req.params.id;
  const { title, description, videoUrl, thumbnailUrl, categoryId, isPublished } = req.body;

  try {
    const updatedVideo = await Video.findByIdAndUpdate(
      videoId,
      { title, description, videoUrl, thumbnailUrl, categoryId, isPublished },
      { new: true }
    );

    if (!updatedVideo) return res.status(404).json({ message: 'Video not found' });

    // Invalidate caches
    await delWithCache('videos:all');
    await delWithCache(`videos:category:${updatedVideo.categoryId}`);
    await delWithCache(`videos:search:*`); // optional: wildcard invalidate if supported

    res.json(updatedVideo);
  } catch (error) {
    res.status(500).json({ message: 'Error updating video', error: error.message });
  }
};

// DELETE: Delete video
exports.deleteVideo = async (req, res) => {
  const videoId = req.params.id;

  try {
    const video = await Video.findByIdAndDelete(videoId);
    await Rating.deleteMany({ videoId });

    if (!video) return res.status(404).json({ message: 'Video not found' });

    // Delete video file
    if (video.videoUrl) {
      const filePath = path.join(__dirname, '..', video.videoUrl);
      if (fs.existsSync(filePath)) fs.unlinkSync(filePath);
    }

    // Invalidate related caches
    await delWithCache('videos:all');
    await delWithCache(`videos:category:${video.categoryId}`);
    await delWithCache(`videos:search:*`);

    res.json({ message: 'Video deleted successfully' });
  } catch (error) {
    res.status(500).json({ message: 'Error deleting video', error: error.message });
  }
};
