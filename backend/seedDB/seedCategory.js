const mongoose = require('mongoose');
const dotenv = require('dotenv');
const path = require('path');

dotenv.config({ path: path.resolve(__dirname, '../.env') });
const Category = require('../models/Category');

mongoose.connect(process.env.MONGO_URI);

const category = new Category({
    name: 'Web 2',
    description: 'All about the latest in web development 2',
    parentCategory: "686cd66a871098765f5acbde", // Assuming this is a top-level category
    isActive: true,
    createdAt: new Date(),
});
  
  category.save()
    .then(() => {
      console.log('Category seeded successfully');
      mongoose.connection.close();
    })
    .catch(err => {
      console.error('Error seeding category:', err);
      mongoose.connection.close();
    });
    