const express = require('express');
const router = express.Router();
const adminController = require('../controllers/adminController');
const { protect } = require('../middleware/authMiddleware');

// User Management
router.get('/users', protect, adminController.getAllUsers);
router.put('/users/:id', protect, adminController.updateUser);
router.delete('/users/:id', protect, adminController.deleteUser);
router.get('/users/stats', protect, adminController.getUserStats);

// Analytics
router.get('/analytics/dashboard', protect, adminController.getDashboardAnalytics);
router.get('/analytics/videos', protect, adminController.getVideoAnalytics);
router.get('/analytics/engagement', protect, adminController.getUserEngagement);

// Category & Video Management
router.get('/categories/stats', protect, adminController.getCategoriesWithStats);
router.delete('/categories/:id', protect, adminController.deleteCategory);
router.get('/videos/stats', protect, adminController.getVideosWithStats);
router.delete('/videos/:id', protect, adminController.deleteVideo);

// Feedback
router.get('/feedback', protect, adminController.getAllFeedback);

module.exports = router;
