import { NextRequest, NextResponse } from 'next/server';
import { getServerSession } from 'next-auth';
import { authOptions } from '@/lib/auth';
import prisma from '@/lib/prisma';

// GET all quizzes
export async function GET() {
  try {
    const quizzes = await prisma.quiz.findMany({
      include: {
        lesson: {
          include: {
            course: true,
          },
        },
        questions: {
          include: {
            options: true,
          },
        },
      },
    });

    return NextResponse.json(quizzes);
  } catch (error) {
    console.error('Error fetching quizzes:', error);
    return NextResponse.json(
      { error: 'Internal server error' },
      { status: 500 }
    );
  }
}

// POST create new quiz (admin only)
export async function POST(request: NextRequest) {
  try {
    const session = await getServerSession(authOptions);

    if (!session?.user?.isAdmin) {
      return NextResponse.json(
        { error: 'Unauthorized' },
        { status: 401 }
      );
    }

    const body = await request.json();
    const { title, lessonId, questions } = body;

    if (!title || !lessonId) {
      return NextResponse.json(
        { error: 'Title and lessonId are required' },
        { status: 400 }
      );
    }

    const quiz = await prisma.quiz.create({
      data: {
        title,
        lessonId,
        questions: questions
          ? {
              create: questions.map(
                (q: {
                  questionText: string;
                  questionType?: string;
                  options?: { optionText: string; isCorrect: boolean }[];
                }) => ({
                  questionText: q.questionText,
                  questionType: q.questionType || 'multiple_choice',
                  options: q.options
                    ? {
                        create: q.options.map((o) => ({
                          optionText: o.optionText,
                          isCorrect: o.isCorrect,
                        })),
                      }
                    : undefined,
                })
              ),
            }
          : undefined,
      },
      include: {
        questions: {
          include: {
            options: true,
          },
        },
      },
    });

    return NextResponse.json(quiz, { status: 201 });
  } catch (error) {
    console.error('Error creating quiz:', error);
    return NextResponse.json(
      { error: 'Internal server error' },
      { status: 500 }
    );
  }
}
