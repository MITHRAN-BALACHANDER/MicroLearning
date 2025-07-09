const Category = require('../models/Category');
const Video = require('../models/Video');

// Utility function (recursive)
const getNestedCategories = async (parentId = null) => {
  const categories = await Category.find({ parentCategory: parentId }).lean();

  for (let category of categories) {
    category.children = await getNestedCategories(category._id);
  }

  return categories;
};

// Controller: Get all categories (flat)
exports.getParentCategories = async (req, res) => {
  try {
    const categories = await Category.find({ parentCategory: {$eq: null}});
    res.json(categories);
  } catch (error) {
    res.status(500).json({ message: 'Error fetching categories', error: error.message });
  }
};

// Controller: Get a category by ID
exports.getCategoryById = async (req, res) => {
  try {
    const { id } = req.params;
    const category = await Category.findById(id);
    if (!category) {
      return res.status(404).json({ message: 'Category not found' });
    }
    res.json(category);
  } catch (error) {
    res.status(500).json({ message: 'Error fetching category', error: error.message });
  }
};

// Controller: Get categories as a tree (nested)
exports.getNestedCategories = async (req, res) => {
  try {
    const nested = await getNestedCategories(); 
    res.json(nested);
  } catch (error) {
    res.status(500).json({ message: 'Error building nested categories', error: error.message });
  }
};

// Controller: Create a new category
exports.createCategory = async (req, res) => {
  try {
    const { name, description, parentCategory, isActive } = req.body;

    const newCategory = new Category({
      name,
      description,
      parentCategory,
      isActive
    });

    await newCategory.save();
    res.status(201).json(newCategory);
  } catch (error) {
    res.status(500).json({ message: 'Error creating category', error: error.message});
  }
};

// Controller: Update a category
exports.updateCategory = async (req, res) => {
  try {
    const { id } = req.params;
    const { name, description, parentCategory, isActive } = req.body;

    const updatedCategory = await Category.findByIdAndUpdate(
      id,
      { name, description, parentCategory, isActive },
      { new: true }
    );

    if (!updatedCategory) {
      return res.status(404).json({ message: 'Category not found' });
    }
    res.json(updatedCategory);
  } catch (error) {
    res.status(500).json({ message: 'Error updating category', error: error.message });
  }
};

// Utility to collect all nested category IDs
const collectCategoryIds = async (parentId) => {
  const ids = [parentId];
  const children = await Category.find({ parentCategory: parentId }).lean();

  for (const child of children) {
    const childIds = await collectCategoryIds(child._id);
    ids.push(...childIds);
  }

  return ids;
};

exports.deleteCategory = async (req, res) => {
  try {
    const { id } = req.params;

    const category = await Category.findById(id);
    if (!category) {
      return res.status(404).json({ message: 'Category not found' });
    }

    // Step 1: Collect all category IDs to delete
    const allCategoryIds = await collectCategoryIds(id);

    // Step 2: Delete all videos related to these categories
    await Video.deleteMany({ categoryId: { $in: allCategoryIds } });

    // Step 3: Delete all categories
    await Category.deleteMany({ _id: { $in: allCategoryIds } });

    res.json({
      message: 'Category, its subcategories, and associated videos deleted successfully'
    });
  } catch (error) {
    res.status(500).json({
      message: 'Error deleting category and videos',
      error: error.message
    });
  }
};
