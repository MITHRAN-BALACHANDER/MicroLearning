import { NextRequest, NextResponse } from 'next/server';
import { getServerSession } from 'next-auth';
import { authOptions } from '@/lib/auth';
import prisma from '@/lib/prisma';

// POST submit quiz answers
export async function POST(
  request: NextRequest,
  { params }: { params: Promise<{ id: string }> }
) {
  try {
    const session = await getServerSession(authOptions);

    if (!session?.user?.id) {
      return NextResponse.json(
        { error: 'Unauthorized' },
        { status: 401 }
      );
    }

    const { id } = await params;
    const quizId = parseInt(id);
    const body = await request.json();
    const { answers } = body; // { questionId: selectedOptionId }

    // Get quiz with questions and options
    const quiz = await prisma.quiz.findUnique({
      where: { id: quizId },
      include: {
        questions: {
          include: {
            options: true,
          },
        },
      },
    });

    if (!quiz) {
      return NextResponse.json(
        { error: 'Quiz not found' },
        { status: 404 }
      );
    }

    // Calculate score
    let correctAnswers = 0;
    const maxScore = quiz.questions.length;

    for (const question of quiz.questions) {
      const selectedOptionId = answers[question.id];
      if (selectedOptionId) {
        const correctOption = question.options.find((o) => o.isCorrect);
        if (correctOption && correctOption.id === selectedOptionId) {
          correctAnswers++;
        }
      }
    }

    const score = (correctAnswers / maxScore) * 100;

    // Save quiz attempt
    const attempt = await prisma.quizAttempt.create({
      data: {
        userId: parseInt(session.user.id),
        quizId,
        score,
        maxScore,
      },
    });

    return NextResponse.json({
      attempt,
      score,
      correctAnswers,
      totalQuestions: maxScore,
      percentage: score.toFixed(1),
    });
  } catch (error) {
    console.error('Error submitting quiz:', error);
    return NextResponse.json(
      { error: 'Internal server error' },
      { status: 500 }
    );
  }
}
