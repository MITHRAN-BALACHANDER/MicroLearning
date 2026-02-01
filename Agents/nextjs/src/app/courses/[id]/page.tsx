import Link from 'next/link';
import { notFound } from 'next/navigation';
import Navbar from '@/components/Navbar';
import Footer from '@/components/Footer';
import prisma from '@/lib/prisma';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { Button } from '@/components/ui/button';
import { Separator } from '@/components/ui/separator';
import { 
  BookOpen, 
  Clock, 
  ArrowLeft, 
  ChevronRight, 
  CheckCircle2,
  PlayCircle
} from 'lucide-react';

interface CoursePageProps {
  params: Promise<{ id: string }>;
}

async function getCourse(id: number) {
  const course = await prisma.course.findUnique({
    where: { id },
    include: {
      lessons: {
        orderBy: { orderIndex: 'asc' },
        include: {
          quizzes: true,
        },
      },
    },
  });
  return course;
}

export default async function CoursePage({ params }: CoursePageProps) {
  const { id } = await params;
  const courseId = parseInt(id);
  const course = await getCourse(courseId);

  if (!course) {
    notFound();
  }

  const totalQuizzes = course.lessons.reduce((sum, lesson) => sum + lesson.quizzes.length, 0);
  const estimatedTime = course.lessons.length * 5;

  return (
    <div className="min-h-screen flex flex-col">
      <Navbar />
      <main className="flex-grow bg-muted/30 py-8">
        <div className="container mx-auto px-4 max-w-4xl">
          {/* Back Button */}
          <Button variant="ghost" size="sm" asChild className="mb-6">
            <Link href="/courses">
              <ArrowLeft className="h-4 w-4 mr-2" />
              Back to Courses
            </Link>
          </Button>

          {/* Course Header Card */}
          <Card className="mb-8 overflow-hidden">
            <div className="h-32 bg-gradient-to-br from-primary to-primary/80" />
            <CardHeader className="relative pb-4">
              <div className="absolute -top-12 left-6">
                <div className="h-20 w-20 rounded-xl bg-background shadow-lg flex items-center justify-center border">
                  <BookOpen className="h-10 w-10 text-primary" />
                </div>
              </div>
              <div className="pt-10">
                <CardTitle className="text-3xl mb-2">{course.title}</CardTitle>
                <p className="text-muted-foreground">
                  {course.description || 'Start your learning journey with this comprehensive course.'}
                </p>
              </div>
            </CardHeader>
            <CardContent>
              <div className="flex flex-wrap gap-4">
                <Badge variant="secondary" className="text-sm py-1 px-3">
                  <BookOpen className="h-3.5 w-3.5 mr-1.5" />
                  {course.lessons.length} lesson{course.lessons.length !== 1 ? 's' : ''}
                </Badge>
                <Badge variant="secondary" className="text-sm py-1 px-3">
                  <Clock className="h-3.5 w-3.5 mr-1.5" />
                  ~{estimatedTime} min total
                </Badge>
                {totalQuizzes > 0 && (
                  <Badge variant="secondary" className="text-sm py-1 px-3">
                    <CheckCircle2 className="h-3.5 w-3.5 mr-1.5" />
                    {totalQuizzes} quiz{totalQuizzes !== 1 ? 'zes' : ''}
                  </Badge>
                )}
              </div>
            </CardContent>
          </Card>

          {/* Course Content */}
          <Card>
            <CardHeader>
              <CardTitle className="text-xl">Course Content</CardTitle>
            </CardHeader>
            <Separator />
            {course.lessons.length === 0 ? (
              <CardContent className="py-12 text-center">
                <div className="h-16 w-16 rounded-full bg-muted flex items-center justify-center mx-auto mb-4">
                  <BookOpen className="h-8 w-8 text-muted-foreground" />
                </div>
                <p className="text-muted-foreground">No lessons available yet.</p>
              </CardContent>
            ) : (
              <div className="divide-y">
                {course.lessons.map((lesson, index) => (
                  <Link
                    key={lesson.id}
                    href={`/courses/${course.id}/lessons/${lesson.id}`}
                    className="flex items-center gap-4 p-4 hover:bg-muted/50 transition-colors group"
                  >
                    <div className="flex-shrink-0 h-10 w-10 rounded-full bg-primary/10 text-primary flex items-center justify-center font-semibold text-sm">
                      {index + 1}
                    </div>
                    <div className="flex-grow min-w-0">
                      <h3 className="font-medium group-hover:text-primary transition-colors truncate">
                        {lesson.title}
                      </h3>
                      <div className="flex items-center gap-3 text-sm text-muted-foreground mt-0.5">
                        <span className="flex items-center gap-1">
                          <Clock className="h-3 w-3" />
                          ~5 min
                        </span>
                        {lesson.quizzes.length > 0 && (
                          <span className="flex items-center gap-1">
                            <CheckCircle2 className="h-3 w-3" />
                            {lesson.quizzes.length} quiz{lesson.quizzes.length !== 1 ? 'zes' : ''}
                          </span>
                        )}
                      </div>
                    </div>
                    <ChevronRight className="h-5 w-5 text-muted-foreground group-hover:text-primary group-hover:translate-x-1 transition-all flex-shrink-0" />
                  </Link>
                ))}
              </div>
            )}
          </Card>

          {/* Start Learning CTA */}
          {course.lessons.length > 0 && (
            <div className="mt-8 text-center">
              <Button size="lg" asChild>
                <Link href={`/courses/${course.id}/lessons/${course.lessons[0].id}`}>
                  <PlayCircle className="h-5 w-5 mr-2" />
                  Start Learning
                </Link>
              </Button>
            </div>
          )}
        </div>
      </main>
      <Footer />
    </div>
  );
}
