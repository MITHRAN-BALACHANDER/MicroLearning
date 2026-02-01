import Link from 'next/link';
import { notFound } from 'next/navigation';
import Navbar from '@/components/Navbar';
import Footer from '@/components/Footer';
import prisma from '@/lib/prisma';
import LessonContent from '@/components/LessonContent';

interface LessonPageProps {
  params: Promise<{ id: string; lessonId: string }>;
}

async function getLesson(lessonId: number, courseId: number) {
  const lesson = await prisma.lesson.findFirst({
    where: {
      id: lessonId,
      courseId: courseId,
    },
    include: {
      course: true,
      quizzes: {
        include: {
          questions: {
            include: {
              options: true,
            },
          },
        },
      },
    },
  });
  return lesson;
}

async function getAdjacentLessons(courseId: number, orderIndex: number) {
  const [previous, next] = await Promise.all([
    prisma.lesson.findFirst({
      where: {
        courseId,
        orderIndex: { lt: orderIndex },
      },
      orderBy: { orderIndex: 'desc' },
    }),
    prisma.lesson.findFirst({
      where: {
        courseId,
        orderIndex: { gt: orderIndex },
      },
      orderBy: { orderIndex: 'asc' },
    }),
  ]);
  return { previous, next };
}

export default async function LessonPage({ params }: LessonPageProps) {
  const { id, lessonId } = await params;
  const courseId = parseInt(id);
  const lessonIdNum = parseInt(lessonId);
  
  const lesson = await getLesson(lessonIdNum, courseId);

  if (!lesson) {
    notFound();
  }

  const { previous, next } = await getAdjacentLessons(
    courseId,
    lesson.orderIndex
  );

  return (
    <div className="min-h-screen flex flex-col">
      <Navbar />
      <main className="flex-grow bg-gray-50 py-8">
        <div className="max-w-4xl mx-auto px-4">
          {/* Breadcrumb */}
          <nav className="mb-6">
            <ol className="flex items-center space-x-2 text-sm text-gray-500">
              <li>
                <Link href="/courses" className="hover:text-indigo-600">
                  Courses
                </Link>
              </li>
              <li>/</li>
              <li>
                <Link
                  href={`/courses/${lesson.course.id}`}
                  className="hover:text-indigo-600"
                >
                  {lesson.course.title}
                </Link>
              </li>
              <li>/</li>
              <li className="text-gray-900 font-medium">{lesson.title}</li>
            </ol>
          </nav>

          {/* Lesson Content */}
          <LessonContent
            lesson={lesson}
            courseId={courseId}
            previousLesson={previous}
            nextLesson={next}
          />
        </div>
      </main>
      <Footer />
    </div>
  );
}
