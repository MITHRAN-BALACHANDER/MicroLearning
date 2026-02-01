# MicroLearning Platform - Next.js

This project is a microlearning platform converted from Flask to Next.js 14 with TypeScript.

## Tech Stack
- **Framework**: Next.js 14 with App Router
- **Language**: TypeScript
- **Styling**: Tailwind CSS
- **Database**: SQLite with Prisma ORM
- **Authentication**: NextAuth.js
- **UI Components**: Custom React components

## Project Structure
- `/src/app` - Next.js App Router pages and API routes
- `/src/components` - Reusable React components
- `/lib` - Utility functions and configurations
- `/prisma` - Database schema and migrations
- `/types` - TypeScript type definitions

## Features
- User authentication (login/register)
- Admin dashboard for content management
- Course and lesson management
- Quiz system with multiple question types
- User progress tracking
- Responsive design with Tailwind CSS

## Development Guidelines
- Use TypeScript for all files
- Follow React best practices
- Use Tailwind CSS for styling
- Keep API routes in `/src/app/api`
- Use Prisma for all database operations
- Use NextAuth.js for authentication

## API Routes
- `/api/auth/[...nextauth]` - Authentication endpoints
- `/api/auth/register` - User registration
- `/api/courses` - Course CRUD operations
- `/api/courses/[id]/lessons` - Lesson management
- `/api/quizzes` - Quiz management
- `/api/quizzes/[id]/submit` - Quiz submission
- `/api/progress` - User progress tracking
- `/api/admin/stats` - Admin statistics
- `/api/admin/users` - User management (admin)

## Database Models
- User - User accounts with admin flag
- Course - Learning courses
- Lesson - Course lessons with content
- Quiz - Quizzes attached to lessons
- Question - Quiz questions
- Option - Multiple choice options
- UserProgress - Track lesson completion
- QuizAttempt - Track quiz attempts and scores
