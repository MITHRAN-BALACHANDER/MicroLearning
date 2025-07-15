const express = require('express');
const router = express.Router();
const videoController = require('../controllers/videoController');
const { protect, admin } = require('../middleware/authMiddleware');
const upload = require('../middleware/upload');

// Get videos by category (protected)
router.get('/category/:categoryId', protect, videoController.getVideosByCategory);

// Search videos by title (protected)
router.get('/search', protect, videoController.searchVideos);

// Get all videos (protected)
router.get('/', protect, videoController.getAllVideos);

// Create a new video (protected, admin only)
// Note: Authentication middleware should come before file upload middleware
router.post('/', protect, admin, (req, res, next) => {
  upload.single('videoFile')(req, res, (err) => {
    if (err) {
      return next(err);
    }
    next();
  });
}, videoController.createVideo);

// Update a video by ID (protected, admin only)
router.patch('/:id', protect, admin, videoController.updateVideo);

// Delete a video by ID (protected, admin only)
router.delete('/:id', protect, admin, videoController.deleteVideo);

module.exports = router;