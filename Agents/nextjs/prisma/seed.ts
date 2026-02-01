import { PrismaClient } from '@prisma/client';
import bcrypt from 'bcryptjs';

const prisma = new PrismaClient();

async function main() {
  // Admin user credentials
  const adminEmail = 'admin@microlearning.com';
  const adminUsername = 'admin';
  const adminPassword = 'Admin123!';

  // Check if admin already exists by email or username
  const existingAdminByEmail = await prisma.user.findUnique({
    where: { email: adminEmail },
  });

  const existingAdminByUsername = await prisma.user.findUnique({
    where: { username: adminUsername },
  });

  if (existingAdminByEmail || existingAdminByUsername) {
    // Update existing user to be admin
    const existingUser = existingAdminByEmail || existingAdminByUsername;
    await prisma.user.update({
      where: { id: existingUser!.id },
      data: { isAdmin: true },
    });
    console.log('✅ Existing user promoted to admin!');
    console.log('━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━');
    console.log(`📧 Email:    ${existingUser!.email}`);
    console.log(`👤 Username: ${existingUser!.username}`);
    console.log('🔑 Password: (use your existing password)');
    console.log('━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━');
    return;
  }

  // Hash password
  const passwordHash = await bcrypt.hash(adminPassword, 10);

  // Create admin user
  const admin = await prisma.user.create({
    data: {
      username: adminUsername,
      email: adminEmail,
      passwordHash: passwordHash,
      isAdmin: true,
    },
  });

  console.log('✅ Admin user created successfully!');
  console.log('━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━');
  console.log('📧 Email:    admin@microlearning.com');
  console.log('👤 Username: admin');
  console.log('🔑 Password: Admin123!');
  console.log('━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━');
  console.log('⚠️  Please change the password after first login!');
}

main()
  .catch((e) => {
    console.error('Error seeding database:', e);
    process.exit(1);
  })
  .finally(async () => {
    await prisma.$disconnect();
  });
