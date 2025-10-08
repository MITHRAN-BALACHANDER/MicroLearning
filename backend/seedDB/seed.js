const mongoose = require('mongoose');
const dotenv = require('dotenv');
const path = require('path');
const bcrypt = require('bcrypt');
const User = require('../models/User');
const Admin = require('../models/Admin');

// Load environment variables from backend/.env
dotenv.config({ path: path.join(__dirname, '../.env') });

const seedDB = async () => {
  try {
    await mongoose.connect(process.env.MONGO_URI);
    await User.deleteMany();
    await Admin.deleteMany();

    const hashedAdminPass = await bcrypt.hash('admin123', 10);
    const hashedUserPass = await bcrypt.hash('user123', 10);

    // 👨‍💼 Create Admins
    const admins = [
      { name: 'Admin User', email: 'admin@example.com', password: hashedAdminPass }
    ];

    // 👥 Create Users
    const users = [
      { name: 'John Doe', email: 'user@example.com', password: hashedUserPass, phone: '+1234567890' },
      { name: 'Jane Smith', email: 'jane@example.com', password: hashedUserPass, phone: '+1234567891' },
      { name: 'Bob Johnson', email: 'bob@example.com', password: hashedUserPass, phone: '+1234567892' },
      { name: 'Alice Williams', email: 'alice@example.com', password: hashedUserPass, phone: '+1234567893' },
      { name: 'Charlie Brown', email: 'charlie@example.com', password: hashedUserPass, phone: '+1234567894' }
    ];

    await Admin.insertMany([...admins]);
    await User.insertMany([...users]);

    console.log('✅ Sample admins and users inserted successfully!');
    console.log('');
    console.log('🔑 Admin Login Credentials:');
    console.log('   Email: admin@example.com');
    console.log('   Password: admin123');
    console.log('');
    console.log('👥 Sample Users Created: ' + users.length);
    process.exit();
  } catch (err) {
    console.error('❌ Error seeding data:', err.message);
    process.exit(1);
  }
};

seedDB();
