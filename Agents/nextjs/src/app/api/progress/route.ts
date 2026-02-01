import { NextRequest, NextResponse } from 'next/server';
import { getServerSession } from 'next-auth';
import { authOptions } from '@/lib/auth';
import prisma from '@/lib/prisma';

// GET user progress
export async function GET() {
  try {
    const session = await getServerSession(authOptions);

    if (!session?.user?.id) {
      return NextResponse.json(
        { error: 'Unauthorized' },
        { status: 401 }
      );
    }

    const userId = parseInt(session.user.id);

    const progress = await prisma.userProgress.findMany({
      where: { userId },
      include: {
        course: true,
        lesson: true,
      },
    });

    // Get quiz attempts
    const quizAttempts = await prisma.quizAttempt.findMany({
      where: { userId },
      include: {
        quiz: {
          include: {
            lesson: {
              include: {
                course: true,
              },
            },
          },
        },
      },
      orderBy: { attemptedAt: 'desc' },
    });

    return NextResponse.json({
      progress,
      quizAttempts,
    });
  } catch (error) {
    console.error('Error fetching progress:', error);
    return NextResponse.json(
      { error: 'Internal server error' },
      { status: 500 }
    );
  }
}

// POST mark lesson as complete
export async function POST(request: NextRequest) {
  try {
    const session = await getServerSession(authOptions);

    if (!session?.user?.id) {
      return NextResponse.json(
        { error: 'Unauthorized' },
        { status: 401 }
      );
    }

    const userId = parseInt(session.user.id);
    const body = await request.json();
    const { lessonId, courseId } = body;

    if (!lessonId || !courseId) {
      return NextResponse.json(
        { error: 'lessonId and courseId are required' },
        { status: 400 }
      );
    }

    // Upsert progress
    const progress = await prisma.userProgress.upsert({
      where: {
        userId_lessonId: {
          userId,
          lessonId,
        },
      },
      update: {
        completed: true,
        completedAt: new Date(),
      },
      create: {
        userId,
        courseId,
        lessonId,
        completed: true,
        completedAt: new Date(),
      },
    });

    return NextResponse.json(progress);
  } catch (error) {
    console.error('Error updating progress:', error);
    return NextResponse.json(
      { error: 'Internal server error' },
      { status: 500 }
    );
  }
}
