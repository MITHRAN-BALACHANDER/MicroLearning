const express = require('express');
const router = express.Router();
const { protect, admin } = require('../middleware/authMiddleware');
const groupController = require('../controllers/groupController');

router.post('/add-member/:groupId', protect, admin, groupController.addMembersToGroup);
router.post('/add-category/:groupId', protect, admin, groupController.addCategoriesToGroup);
router.post('/', protect, admin, groupController.createGroup);

router.get('/', protect, groupController.getGroups);

router.put('/:groupId', protect, admin, groupController.updateGroup);

router.delete('/remove-member/:groupId', protect, admin, groupController.removeMembersFromGroup);
router.delete('/remove-category', protect, admin, groupController.removeCategoriesFromGroup);
router.delete('/:groupId', protect, admin, groupController.deleteGroup);

module.exports = router;