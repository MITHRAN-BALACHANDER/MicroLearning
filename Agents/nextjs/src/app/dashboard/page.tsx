'use client';

import { useEffect, useState } from 'react';
import { useSession } from 'next-auth/react';
import { useRouter } from 'next/navigation';
import Link from 'next/link';
import Navbar from '@/components/Navbar';
import Footer from '@/components/Footer';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { Button } from '@/components/ui/button';
import { Progress } from '@/components/ui/progress';
import { Skeleton } from '@/components/ui/skeleton';
import { Separator } from '@/components/ui/separator';
import { 
  BookOpen, 
  CheckCircle2, 
  Trophy, 
  TrendingUp,
  ArrowRight,
  Clock
} from 'lucide-react';

interface Course {
  id: number;
  title: string;
}

interface Lesson {
  id: number;
  title: string;
}

interface ProgressItem {
  id: number;
  completed: boolean;
  completedAt: string | null;
  course: Course;
  lesson: Lesson | null;
}

interface Quiz {
  title: string;
  lesson: {
    title: string;
    course: Course;
  };
}

interface QuizAttempt {
  id: number;
  score: number;
  maxScore: number;
  attemptedAt: string;
  quiz: Quiz;
}

interface DashboardData {
  progress: ProgressItem[];
  quizAttempts: QuizAttempt[];
}

export default function DashboardPage() {
  const { data: session, status } = useSession();
  const router = useRouter();
  const [data, setData] = useState<DashboardData | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    if (status === 'unauthenticated') {
      router.push('/login');
    }
  }, [status, router]);

  useEffect(() => {
    if (session) {
      fetchProgress();
    }
  }, [session]);

  const fetchProgress = async () => {
    try {
      const response = await fetch('/api/progress');
      if (response.ok) {
        const data = await response.json();
        setData(data);
      }
    } catch (error) {
      console.error('Error fetching progress:', error);
    } finally {
      setLoading(false);
    }
  };

  if (status === 'loading' || loading) {
    return (
      <div className="min-h-screen flex flex-col">
        <Navbar />
        <main className="flex-grow bg-muted/30 py-8">
          <div className="container mx-auto px-4">
            <Skeleton className="h-10 w-64 mb-8" />
            <div className="grid grid-cols-1 md:grid-cols-3 gap-6 mb-8">
              <Skeleton className="h-32" />
              <Skeleton className="h-32" />
              <Skeleton className="h-32" />
            </div>
          </div>
        </main>
      </div>
    );
  }

  if (!session) {
    return null;
  }

  const completedLessons = data?.progress.filter((p) => p.completed) || [];
  const averageQuizScore = data?.quizAttempts.length
    ? (data.quizAttempts.reduce((sum, a) => sum + a.score, 0) / data.quizAttempts.length).toFixed(1)
    : 0;

  return (
    <div className="min-h-screen flex flex-col">
      <Navbar />
      <main className="flex-grow bg-muted/30 py-8">
        <div className="container mx-auto px-4">
          {/* Header */}
          <div className="mb-8">
            <h1 className="text-3xl font-bold mb-2">
              Welcome back, {session.user?.name}! 👋
            </h1>
            <p className="text-muted-foreground">
              Track your learning progress and continue where you left off.
            </p>
          </div>

          {/* Stats Cards */}
          <div className="grid grid-cols-1 md:grid-cols-3 gap-6 mb-8">
            <Card>
              <CardContent className="pt-6">
                <div className="flex items-center gap-4">
                  <div className="h-12 w-12 rounded-lg bg-primary/10 flex items-center justify-center">
                    <CheckCircle2 className="h-6 w-6 text-primary" />
                  </div>
                  <div>
                    <p className="text-sm text-muted-foreground">Lessons Completed</p>
                    <p className="text-3xl font-bold">{completedLessons.length}</p>
                  </div>
                </div>
              </CardContent>
            </Card>

            <Card>
              <CardContent className="pt-6">
                <div className="flex items-center gap-4">
                  <div className="h-12 w-12 rounded-lg bg-emerald-500/10 flex items-center justify-center">
                    <BookOpen className="h-6 w-6 text-emerald-500" />
                  </div>
                  <div>
                    <p className="text-sm text-muted-foreground">Quizzes Taken</p>
                    <p className="text-3xl font-bold">{data?.quizAttempts.length || 0}</p>
                  </div>
                </div>
              </CardContent>
            </Card>

            <Card>
              <CardContent className="pt-6">
                <div className="flex items-center gap-4">
                  <div className="h-12 w-12 rounded-lg bg-amber-500/10 flex items-center justify-center">
                    <Trophy className="h-6 w-6 text-amber-500" />
                  </div>
                  <div>
                    <p className="text-sm text-muted-foreground">Average Score</p>
                    <p className="text-3xl font-bold">{averageQuizScore}%</p>
                  </div>
                </div>
              </CardContent>
            </Card>
          </div>

          <div className="grid grid-cols-1 lg:grid-cols-2 gap-8">
            {/* Completed Lessons */}
            <Card>
              <CardHeader className="pb-3">
                <div className="flex items-center justify-between">
                  <CardTitle className="text-lg">Completed Lessons</CardTitle>
                  <Badge variant="secondary">{completedLessons.length} total</Badge>
                </div>
              </CardHeader>
              <Separator />
              <CardContent className="pt-4">
                {completedLessons.length === 0 ? (
                  <div className="text-center py-8">
                    <div className="h-12 w-12 rounded-full bg-muted flex items-center justify-center mx-auto mb-3">
                      <BookOpen className="h-6 w-6 text-muted-foreground" />
                    </div>
                    <p className="text-muted-foreground mb-4">No lessons completed yet.</p>
                    <Button variant="outline" size="sm" asChild>
                      <Link href="/courses">
                        Start learning
                        <ArrowRight className="ml-2 h-4 w-4" />
                      </Link>
                    </Button>
                  </div>
                ) : (
                  <div className="space-y-3 max-h-80 overflow-y-auto pr-2">
                    {completedLessons.map((progress) => (
                      <div key={progress.id} className="flex items-center gap-3 p-3 rounded-lg bg-muted/50">
                        <div className="h-8 w-8 rounded-full bg-emerald-500/20 flex items-center justify-center flex-shrink-0">
                          <CheckCircle2 className="h-4 w-4 text-emerald-500" />
                        </div>
                        <div className="flex-grow min-w-0">
                          <p className="font-medium text-sm truncate">
                            {progress.lesson?.title || 'Unknown Lesson'}
                          </p>
                          <p className="text-xs text-muted-foreground truncate">
                            {progress.course.title}
                          </p>
                        </div>
                      </div>
                    ))}
                  </div>
                )}
              </CardContent>
            </Card>

            {/* Recent Quiz Attempts */}
            <Card>
              <CardHeader className="pb-3">
                <div className="flex items-center justify-between">
                  <CardTitle className="text-lg">Recent Quiz Results</CardTitle>
                  <Badge variant="secondary">{data?.quizAttempts.length || 0} total</Badge>
                </div>
              </CardHeader>
              <Separator />
              <CardContent className="pt-4">
                {!data?.quizAttempts.length ? (
                  <div className="text-center py-8">
                    <div className="h-12 w-12 rounded-full bg-muted flex items-center justify-center mx-auto mb-3">
                      <Trophy className="h-6 w-6 text-muted-foreground" />
                    </div>
                    <p className="text-muted-foreground mb-4">No quizzes taken yet.</p>
                    <Button variant="outline" size="sm" asChild>
                      <Link href="/courses">
                        Take a quiz
                        <ArrowRight className="ml-2 h-4 w-4" />
                      </Link>
                    </Button>
                  </div>
                ) : (
                  <div className="space-y-3 max-h-80 overflow-y-auto pr-2">
                    {data.quizAttempts.slice(0, 10).map((attempt) => (
                      <div key={attempt.id} className="flex items-center gap-3 p-3 rounded-lg bg-muted/50">
                        <div className={`h-8 w-8 rounded-full flex items-center justify-center flex-shrink-0 ${
                          attempt.score >= 70 ? 'bg-emerald-500/20' : 'bg-destructive/20'
                        }`}>
                          <TrendingUp className={`h-4 w-4 ${
                            attempt.score >= 70 ? 'text-emerald-500' : 'text-destructive'
                          }`} />
                        </div>
                        <div className="flex-grow min-w-0">
                          <p className="font-medium text-sm truncate">
                            {attempt.quiz.title}
                          </p>
                          <p className="text-xs text-muted-foreground truncate">
                            {attempt.quiz.lesson.course.title}
                          </p>
                        </div>
                        <Badge variant={attempt.score >= 70 ? 'success' : 'destructive'}>
                          {attempt.score.toFixed(0)}%
                        </Badge>
                      </div>
                    ))}
                  </div>
                )}
              </CardContent>
            </Card>
          </div>

          {/* Continue Learning CTA */}
          <Card className="mt-8 bg-gradient-to-r from-primary/10 to-primary/5">
            <CardContent className="py-8">
              <div className="flex flex-col md:flex-row items-center justify-between gap-4">
                <div>
                  <h3 className="text-xl font-semibold mb-1">Ready to continue learning?</h3>
                  <p className="text-muted-foreground">
                    Pick up where you left off or explore new courses.
                  </p>
                </div>
                <Button size="lg" asChild>
                  <Link href="/courses">
                    Browse Courses
                    <ArrowRight className="ml-2 h-4 w-4" />
                  </Link>
                </Button>
              </div>
            </CardContent>
          </Card>
        </div>
      </main>
      <Footer />
    </div>
  );
}
