const express = require('express');
const router = express.Router();
const categoryController = require('../controllers/categoryController');
const { protect, admin } = require('../middleware/authMiddleware');

router.get('/nested', protect, admin, categoryController.getNestedCategories);
router.get('/', protect, admin, categoryController.getParentCategories);
router.get('/:id', protect, admin, categoryController.getCategoryById);
router.post('/', protect, admin, categoryController.createCategory);
router.patch('/:id', protect, admin, categoryController.updateCategory);
router.delete('/:id', protect, admin, categoryController.deleteCategory);

module.exports = router;
