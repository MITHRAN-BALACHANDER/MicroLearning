const express = require('express');
const router = express.Router();

const userController = require('../controllers/userController');
const { protect, admin } = require('../middleware/authMiddleware');


// Create a new user (public)
router.post('/', userController.createUser);

// Get all users (protected, admin only)
router.get('/', protect, admin, userController.getAllUsers);

// Get a single user by ID (protected)
router.get('/:id', protect, userController.getUserById);

// Update a user by ID (protected)
router.put('/:id', protect, userController.updateUserById);

// Delete a user by ID (protected, admin only)
router.delete('/:id', protect, admin, userController.deleteUserById);

module.exports = router;
