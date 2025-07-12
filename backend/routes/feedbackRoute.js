const express = require('express');
const router = express.Router();
const { protect } = require('../middleware/authMiddleware');

const feedbackController = require('../controllers/feedbackController');

// Create feedback (protected)
router.post('/', protect, feedbackController.createFeedback);
router.get('/', protect, feedbackController.getFeedbacks);

module.exports = router;