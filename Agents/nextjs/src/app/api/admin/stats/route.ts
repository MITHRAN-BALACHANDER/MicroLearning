import { NextResponse } from 'next/server';
import { getServerSession } from 'next-auth';
import { authOptions } from '@/lib/auth';
import prisma from '@/lib/prisma';

// GET admin dashboard stats
export async function GET() {
  try {
    const session = await getServerSession(authOptions);

    if (!session?.user?.isAdmin) {
      return NextResponse.json(
        { error: 'Unauthorized' },
        { status: 401 }
      );
    }

    const [
      totalUsers,
      totalCourses,
      totalLessons,
      totalQuizzes,
      recentUsers,
      recentAttempts,
    ] = await Promise.all([
      prisma.user.count(),
      prisma.course.count(),
      prisma.lesson.count(),
      prisma.quiz.count(),
      prisma.user.findMany({
        orderBy: { createdAt: 'desc' },
        take: 5,
        select: {
          id: true,
          username: true,
          email: true,
          createdAt: true,
          isAdmin: true,
        },
      }),
      prisma.quizAttempt.findMany({
        orderBy: { attemptedAt: 'desc' },
        take: 10,
        include: {
          user: {
            select: {
              username: true,
            },
          },
          quiz: {
            select: {
              title: true,
            },
          },
        },
      }),
    ]);

    return NextResponse.json({
      stats: {
        totalUsers,
        totalCourses,
        totalLessons,
        totalQuizzes,
      },
      recentUsers,
      recentAttempts,
    });
  } catch (error) {
    console.error('Error fetching admin stats:', error);
    return NextResponse.json(
      { error: 'Internal server error' },
      { status: 500 }
    );
  }
}
