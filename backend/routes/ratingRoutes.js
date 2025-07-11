const express = require('express');
const router = express.Router();
const ratingController = require('../controllers/ratingController');
const { protect, admin } = require('../middleware/authMiddleware');

router.post('/', protect, ratingController.createRating);
router.get('/:videoId', protect, ratingController.getRatings);

module.exports = router;
