const mongoose = require('mongoose');
const dotenv = require('dotenv');
const bcrypt = require('bcrypt');
const User = require('../models/User');
const Admin = require('../models/Admin');

dotenv.config();

const seedDB = async () => {
  try {
    await mongoose.connect(process.env.MONGO_URI);
    await User.deleteMany();

    const hashedAdminPass = await bcrypt.hash('admin@123', 10);
    const hashedUserPass = await bcrypt.hash('user@123', 10);

    // 👨‍💼 Create Admins
    const admins = [
      { name: 'Admin One', email: 'admin@example.com', password: hashedAdminPass, role: 'admin' }
    ];

    // 👥 Create Users
    const users = [
      { name: 'User One', email: 'user@example.com', password: hashedUserPass, role: 'user' }
    ];

    await User.insertMany([...users]);
    await Admin.insertMany([...admins]);

    console.log('✅ Sample admins and users inserted successfully!');
    process.exit();
  } catch (err) {
    console.error('❌ Error seeding data:', err.message);
    process.exit(1);
  }
};

seedDB();
