import Link from 'next/link';
import Navbar from '@/components/Navbar';
import Footer from '@/components/Footer';
import prisma from '@/lib/prisma';
import { Card, CardContent, CardFooter, CardHeader } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { Button } from '@/components/ui/button';
import { BookOpen, Clock, ArrowRight, GraduationCap } from 'lucide-react';

interface Course {
  id: number;
  title: string;
  description: string | null;
  imageUrl: string | null;
  _count: {
    lessons: number;
  };
}

async function getCourses(): Promise<Course[]> {
  const courses = await prisma.course.findMany({
    include: {
      _count: {
        select: { lessons: true },
      },
    },
    orderBy: { createdAt: 'desc' },
  });
  return courses;
}

export default async function CoursesPage() {
  const courses = await getCourses();

  return (
    <div className="min-h-screen flex flex-col">
      <Navbar />
      <main className="flex-grow bg-muted/30 py-12">
        <div className="container mx-auto px-4">
          {/* Header */}
          <div className="max-w-2xl mb-12">
            <Badge variant="outline" className="mb-4">Catalog</Badge>
            <h1 className="text-4xl font-bold mb-4">
              Explore Our Courses
            </h1>
            <p className="text-lg text-muted-foreground">
              Discover bite-sized learning experiences designed to help you grow. 
              Each course is carefully crafted for maximum impact in minimum time.
            </p>
          </div>

          {courses.length === 0 ? (
            <Card className="max-w-md mx-auto text-center">
              <CardContent className="pt-12 pb-8">
                <div className="h-16 w-16 rounded-full bg-muted flex items-center justify-center mx-auto mb-4">
                  <BookOpen className="h-8 w-8 text-muted-foreground" />
                </div>
                <h3 className="text-lg font-semibold mb-2">No courses available yet</h3>
                <p className="text-muted-foreground mb-6">
                  We&apos;re working on adding new courses. Check back soon!
                </p>
                <Button variant="outline" asChild>
                  <Link href="/">Go Home</Link>
                </Button>
              </CardContent>
            </Card>
          ) : (
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
              {courses.map((course) => (
                <Link key={course.id} href={`/courses/${course.id}`}>
                  <Card className="h-full hover:shadow-lg transition-all duration-300 hover:-translate-y-1 overflow-hidden group">
                    {/* Course Image/Banner */}
                    <div className="h-48 bg-gradient-to-br from-primary/80 to-primary flex items-center justify-center relative overflow-hidden">
                      {course.imageUrl ? (
                        <img
                          src={course.imageUrl}
                          alt={course.title}
                          className="w-full h-full object-cover"
                        />
                      ) : (
                        <GraduationCap className="h-16 w-16 text-primary-foreground/50" />
                      )}
                      <div className="absolute inset-0 bg-gradient-to-t from-black/60 to-transparent" />
                      <Badge className="absolute top-4 right-4" variant="secondary">
                        {course._count.lessons} lesson{course._count.lessons !== 1 ? 's' : ''}
                      </Badge>
                    </div>
                    
                    <CardHeader className="pb-2">
                      <h2 className="text-xl font-semibold line-clamp-2 group-hover:text-primary transition-colors">
                        {course.title}
                      </h2>
                    </CardHeader>
                    
                    <CardContent className="pb-4">
                      <p className="text-muted-foreground text-sm line-clamp-2">
                        {course.description || 'Start your learning journey with this course.'}
                      </p>
                    </CardContent>
                    
                    <CardFooter className="pt-0 flex items-center justify-between">
                      <div className="flex items-center gap-4 text-sm text-muted-foreground">
                        <div className="flex items-center gap-1">
                          <BookOpen className="h-4 w-4" />
                          <span>{course._count.lessons} lessons</span>
                        </div>
                        <div className="flex items-center gap-1">
                          <Clock className="h-4 w-4" />
                          <span>~{course._count.lessons * 5} min</span>
                        </div>
                      </div>
                      <ArrowRight className="h-4 w-4 text-muted-foreground group-hover:text-primary group-hover:translate-x-1 transition-all" />
                    </CardFooter>
                  </Card>
                </Link>
              ))}
            </div>
          )}
        </div>
      </main>
      <Footer />
    </div>
  );
}
