const Video = require('../models/Video');
const Rating = require('../models/Rating');
const fs = require('fs');
const path = require('path');

exports.getVideosByCategory = async (req, res) => {
  try {
    const videos = await Video.find({ categoryId: req.params.categoryId });
    res.json(videos);
  } catch (error) {
    res.status(500).json({ message: 'Error fetching videos by category', error: error.message });
  }
}

exports.searchVideos = async (req, res) => {
  try {
    const { query } = req.query;
    const videos = await Video.find({ title: { $regex: query, $options: 'i' } });
    res.json(videos);
  } catch (error) {
    res.status(500).json({ message: 'Error searching videos', error: error.message });
  }
}

exports.getAllVideos = async (req, res) => {
  try {
    const videos = await Video.find();
    res.json(videos);
  } catch (error) {
    res.status(500).json({ message: 'Error fetching videos', error: error.message });
  }
}

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
    res.status(201).json(newVideo);
  } catch (error) {
    res.status(500).json({ message: 'Error creating video', error: error.message });
  }
}

exports.updateVideo = async (req, res) => {
  try {
    const { title, description, videoUrl, thumbnailUrl, categoryId, isPublished } = req.body;

    const updatedVideo = await Video.findByIdAndUpdate(
      req.params.id,
      { title, description, videoUrl, thumbnailUrl, categoryId, isPublished },
      { new: true }
    );

    if (!updatedVideo) {
      return res.status(404).json({ message: 'Video not found' });
    }

    res.json(updatedVideo);
  } catch (error) {
    res.status(500).json({ message: 'Error updating video', error: error.message });
  }
}

exports.deleteVideo = async (req, res) => {
  try {
    const video = await Video.findByIdAndDelete(req.params.id);
    await Rating.deleteMany({ videoId: req.params.id });

    if (!video) {
      return res.status(404).json({ message: 'Video not found' });
    }

    // Delete video file from uploads folder
    if (video.videoUrl) {
      const filePath = path.join(__dirname, '..', video.videoUrl);
      if (fs.existsSync(filePath)) {
        fs.unlinkSync(filePath);
      }
    }

    res.json({ message: 'Video deleted successfully' });
  } catch (error) {
    res.status(500).json({ message: 'Error deleting video', error: error.message });
  }
};

