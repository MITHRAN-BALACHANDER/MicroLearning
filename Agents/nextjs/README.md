# MicroLearning Platform

A microlearning platform built with Next.js 14, TypeScript, Prisma, and NextAuth.js. Features bite-sized lessons, interactive quizzes, and progress tracking.

## Features

- 🔐 **Authentication**: User registration and login with NextAuth.js
-   **Course Management**: Create and manage courses with lessons
-   **Quizzes**: Multiple choice quizzes with scoring
-   **Progress Tracking**: Track lesson completion and quiz scores
- 👤 **Admin Dashboard**: Manage courses, lessons, users, and view statistics
- 📱 **Responsive Design**: Tailwind CSS for mobile-friendly UI

## Tech Stack

- **Framework**: Next.js 14 with App Router
- **Language**: TypeScript
- **Styling**: Tailwind CSS
- **Database**: SQLite with Prisma ORM
- **Authentication**: NextAuth.js

## Getting Started

### Prerequisites

- Node.js 18+
- npm or yarn

### Installation

1. Install dependencies:
```bash
npm install
```

2. Set up the database:
```bash
npx prisma migrate deploy
npx prisma generate
```

3. Create a `.env` file (already included):
```
DATABASE_URL="file:./dev.db"
NEXTAUTH_SECRET="your-secret-key-change-in-production"
NEXTAUTH_URL="http://localhost:3000"
```

4. Run the development server:
```bash
npm run dev
```

5. Open [http://localhost:3000](http://localhost:3000) in your browser.

## Project Structure

```
src/
├── app/                    # Next.js App Router
│   ├── api/                # API routes
│   │   ├── admin/          # Admin endpoints
│   │   ├── auth/           # Authentication endpoints
│   │   ├── courses/        # Course CRUD
│   │   ├── progress/       # User progress
│   │   └── quizzes/        # Quiz management
│   ├── admin/              # Admin pages
│   ├── courses/            # Course pages
│   ├── dashboard/          # User dashboard
│   ├── login/              # Login page
│   └── register/           # Registration page
├── components/             # React components
│   ├── Footer.tsx
│   ├── LessonContent.tsx
│   ├── Navbar.tsx
│   ├── Providers.tsx
│   └── QuizComponent.tsx
└── lib/                    # Utilities
    ├── auth.ts             # NextAuth configuration
    └── prisma.ts           # Prisma client
prisma/
├── schema.prisma           # Database schema
└── migrations/             # Database migrations
```

## API Routes

| Route | Method | Description |
|-------|--------|-------------|
| `/api/auth/[...nextauth]` | GET/POST | Authentication |
| `/api/auth/register` | POST | User registration |
| `/api/courses` | GET/POST | List/Create courses |
| `/api/courses/[id]` | GET/PUT/DELETE | Course operations |
| `/api/courses/[id]/lessons` | GET/POST | Course lessons |
| `/api/quizzes` | GET/POST | Quiz management |
| `/api/quizzes/[id]/submit` | POST | Submit quiz answers |
| `/api/progress` | GET/POST | User progress |
| `/api/admin/stats` | GET | Dashboard statistics |
| `/api/admin/users` | GET/POST | User management |

## Creating an Admin User

To create an admin user:

1. Register a normal user through the app
2. Use a database tool to update the `is_admin` field to `true` in the `users` table

Or use Prisma Studio:
```bash
npx prisma studio
```

## License

MIT
