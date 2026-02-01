import { NextRequest, NextResponse } from 'next/server';
import { getServerSession } from 'next-auth';
import { authOptions } from '@/lib/auth';
import prisma from '@/lib/prisma';

// GET lessons for a course
export async function GET(
  request: NextRequest,
  { params }: { params: Promise<{ id: string }> }
) {
  try {
    const { id } = await params;
    const courseId = parseInt(id);

    const lessons = await prisma.lesson.findMany({
      where: { courseId },
      orderBy: { orderIndex: 'asc' },
      include: {
        quizzes: true,
      },
    });

    return NextResponse.json(lessons);
  } catch (error) {
    console.error('Error fetching lessons:', error);
    return NextResponse.json(
      { error: 'Internal server error' },
      { status: 500 }
    );
  }
}

// POST create new lesson (admin only)
export async function POST(
  request: NextRequest,
  { params }: { params: Promise<{ id: string }> }
) {
  try {
    const session = await getServerSession(authOptions);

    if (!session?.user?.isAdmin) {
      return NextResponse.json(
        { error: 'Unauthorized' },
        { status: 401 }
      );
    }

    const { id } = await params;
    const courseId = parseInt(id);
    const body = await request.json();
    const { title, content, orderIndex } = body;

    if (!title || !content) {
      return NextResponse.json(
        { error: 'Title and content are required' },
        { status: 400 }
      );
    }

    // Get the next order index if not provided
    let order = orderIndex;
    if (order === undefined) {
      const lastLesson = await prisma.lesson.findFirst({
        where: { courseId },
        orderBy: { orderIndex: 'desc' },
      });
      order = lastLesson ? lastLesson.orderIndex + 1 : 0;
    }

    const lesson = await prisma.lesson.create({
      data: {
        title,
        content,
        orderIndex: order,
        courseId,
      },
    });

    return NextResponse.json(lesson, { status: 201 });
  } catch (error) {
    console.error('Error creating lesson:', error);
    return NextResponse.json(
      { error: 'Internal server error' },
      { status: 500 }
    );
  }
}
