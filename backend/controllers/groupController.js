const Group = require('../models/Group');
const User = require('../models/User');
const mongoose = require('mongoose');

exports.createGroup = async (req, res) => {
  try {
    const { name, description } = req.body;
    const group = new Group({ name, description });
    await group.save();
    res.status(201).json({ message: 'Group created successfully', group });
  } catch (error) {
    res.status(500).json({ message: 'Error creating group', error: error.message });
  }
}

exports.getGroups = async (req, res) => {
  try {
    const groups = await Group.find().populate('members', 'username email');
    res.status(200).json(groups);
  } catch (error) {
    res.status(500).json({ message: 'Error fetching groups', error: error.message });
  }
}

exports.updateGroup = async (req, res) => {
  try {
    const { groupId } = req.params;
    const { name, description, isActive } = req.body;
    const group = await Group.findByIdAndUpdate(groupId, { name, description, isActive }, { new: true });
    if (!group) {
      return res.status(404).json({ message: 'Group not found' });
    }
    res.status(200).json({ message: 'Group updated successfully', group });
  } catch (error) {
    res.status(500).json({ message: 'Error updating group', error: error.message });
  }
}

exports.deleteGroup = async (req, res) => {
  try {
    const { groupId } = req.params;
    const group = await Group.findByIdAndDelete(groupId);
    if (!group) {
      return res.status(404).json({ message: 'Group not found' });
    }
    res.status(200).json({ message: 'Group deleted successfully' });
  } catch (error) {
    res.status(500).json({ message: 'Error deleting group', error: error.message });
  }
}

exports.addMembersToGroup = async (req, res) => {
  try {
    const groupId = req.params.groupId;
    const userIds = req.body.userIds;

    if (!mongoose.Types.ObjectId.isValid(groupId) || !Array.isArray(userIds)) {
      return res.status(400).json({ message: 'Invalid groupId or userIds' });
    }

    const group = await Group.findById(groupId);
    if (!group) {
      return res.status(404).json({ message: 'Group not found' });
    }

    const users = await User.find({ _id: { $in: userIds } });
    if (users.length === 0) {
      return res.status(404).json({ message: 'No users found' });
    }

    const existingMemberIds = new Set(group.members.map(id => id.toString()));
    const newMemberIds = users
      .map(user => user._id.toString())
      .filter(id => !existingMemberIds.has(id))
      .map(id => new mongoose.Types.ObjectId(id));

    group.members.push(...newMemberIds);
    await group.save();

    res.status(200).json({ message: 'Users added to group successfully', group });
  } catch (error) {
    res.status(500).json({ message: 'Error adding users to group', error: error.message });
  }
};

exports.removeMembersFromGroup = async (req, res) => {
  try {
    const groupId = req.params.groupId;
    const userIds = req.body.userIds; 
 
    const group = await Group.findById(groupId);
    if (!group) {
      return res.status(404).json({ message: 'Group not found' });
    }
    group.members.pull(...userIds.map(userId => new mongoose.Types.ObjectId(userId)));
    await group.save();
    res.status(200).json({ message: 'Users removed from group successfully', group });
  } catch (error) {
    res.status(500).json({ message: 'Error removing users from group', error: error.message });
  }
}

exports.addCategoriesToGroup = async (req, res) => {
  try {
    const groupId = req.params.groupId;
    const categoryIds = req.body.categoryIds;

    if (!mongoose.Types.ObjectId.isValid(groupId) || !Array.isArray(categoryIds)) {
      return res.status(400).json({ message: 'Invalid groupId or categoryIds' });
    }

    const group = await Group.findById(groupId);
    if (!group) {
      return res.status(404).json({ message: 'Group not found' });
    }

    const existingCategoryIds = new Set(group.category.map(id => id.toString()));
    const newCategoryIds = categoryIds
      .filter(id => mongoose.Types.ObjectId.isValid(id) && !existingCategoryIds.has(id))
      .map(id => new mongoose.Types.ObjectId(id));

    group.category.push(...newCategoryIds);
    await group.save();

    res.status(200).json({ message: 'Categories added to group successfully', group });
  } catch (error) {
    res.status(500).json({ message: 'Error adding categories to group', error: error.message });
  }
};


exports.removeCategoriesFromGroup = async (req, res) => {
  try {
    const groupId = req.params.groupId;
    const categoryIds = req.body.categoryIds;
    const group = await Group.findById(groupId);
    if (!group) {
      return res.status(404).json({ message: 'Group not found' });
    }
    group.category.pull(...categoryIds.map(id => new mongoose.Types.ObjectId(id)));
    await group.save();
    res.status(200).json({ message: 'Categories removed from group successfully', group });
  } catch (error) {
    res.status(500).json({ message: 'Error removing categories from group', error: error.message });
  }
}
