'use client';

import { useEffect, useState } from 'react';
import { useSession } from 'next-auth/react';
import { useRouter } from 'next/navigation';
import Link from 'next/link';
import Navbar from '@/components/Navbar';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { Button } from '@/components/ui/button';
import { Skeleton } from '@/components/ui/skeleton';
import { Separator } from '@/components/ui/separator';
import { 
  Users, 
  BookOpen, 
  FileText, 
  ClipboardList,
  ArrowRight,
  TrendingUp,
  Settings,
  LayoutDashboard
} from 'lucide-react';

interface Stats {
  totalUsers: number;
  totalCourses: number;
  totalLessons: number;
  totalQuizzes: number;
}

interface RecentUser {
  id: number;
  username: string;
  email: string;
  createdAt: string;
  isAdmin: boolean;
}

interface RecentAttempt {
  id: number;
  score: number;
  maxScore: number;
  attemptedAt: string;
  user: { username: string };
  quiz: { title: string };
}

interface AdminData {
  stats: Stats;
  recentUsers: RecentUser[];
  recentAttempts: RecentAttempt[];
}

export default function AdminPage() {
  const { data: session, status } = useSession();
  const router = useRouter();
  const [data, setData] = useState<AdminData | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    if (status === 'unauthenticated') {
      router.push('/login');
    } else if (status === 'authenticated' && !session?.user?.isAdmin) {
      router.push('/dashboard');
    }
  }, [status, session, router]);

  useEffect(() => {
    if (session?.user?.isAdmin) {
      fetchStats();
    }
  }, [session]);

  const fetchStats = async () => {
    try {
      const response = await fetch('/api/admin/stats');
      if (response.ok) {
        const data = await response.json();
        setData(data);
      }
    } catch (error) {
      console.error('Error fetching stats:', error);
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
            <div className="grid grid-cols-1 md:grid-cols-4 gap-6 mb-8">
              <Skeleton className="h-32" />
              <Skeleton className="h-32" />
              <Skeleton className="h-32" />
              <Skeleton className="h-32" />
            </div>
          </div>
        </main>
      </div>
    );
  }

  if (!session?.user?.isAdmin) {
    return null;
  }

  return (
    <div className="min-h-screen flex flex-col">
      <Navbar />
      <main className="flex-grow bg-muted/30 py-8">
        <div className="container mx-auto px-4">
          {/* Header */}
          <div className="flex flex-col md:flex-row md:items-center md:justify-between mb-8 gap-4">
            <div>
              <div className="flex items-center gap-2 mb-2">
                <LayoutDashboard className="h-6 w-6 text-primary" />
                <h1 className="text-3xl font-bold">Admin Dashboard</h1>
              </div>
              <p className="text-muted-foreground">
                Manage your platform and monitor activity.
              </p>
            </div>
            <div className="flex gap-3">
              <Button asChild>
                <Link href="/admin/courses">
                  <BookOpen className="h-4 w-4 mr-2" />
                  Manage Courses
                </Link>
              </Button>
              <Button variant="outline" asChild>
                <Link href="/admin/users">
                  <Users className="h-4 w-4 mr-2" />
                  Manage Users
                </Link>
              </Button>
            </div>
          </div>

          {/* Stats Cards */}
          <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-6 mb-8">
            <Card>
              <CardContent className="pt-6">
                <div className="flex items-center gap-4">
                  <div className="h-12 w-12 rounded-lg bg-blue-500/10 flex items-center justify-center">
                    <Users className="h-6 w-6 text-blue-500" />
                  </div>
                  <div>
                    <p className="text-sm text-muted-foreground">Total Users</p>
                    <p className="text-3xl font-bold">{data?.stats.totalUsers || 0}</p>
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
                    <p className="text-sm text-muted-foreground">Total Courses</p>
                    <p className="text-3xl font-bold">{data?.stats.totalCourses || 0}</p>
                  </div>
                </div>
              </CardContent>
            </Card>

            <Card>
              <CardContent className="pt-6">
                <div className="flex items-center gap-4">
                  <div className="h-12 w-12 rounded-lg bg-amber-500/10 flex items-center justify-center">
                    <FileText className="h-6 w-6 text-amber-500" />
                  </div>
                  <div>
                    <p className="text-sm text-muted-foreground">Total Lessons</p>
                    <p className="text-3xl font-bold">{data?.stats.totalLessons || 0}</p>
                  </div>
                </div>
              </CardContent>
            </Card>

            <Card>
              <CardContent className="pt-6">
                <div className="flex items-center gap-4">
                  <div className="h-12 w-12 rounded-lg bg-purple-500/10 flex items-center justify-center">
                    <ClipboardList className="h-6 w-6 text-purple-500" />
                  </div>
                  <div>
                    <p className="text-sm text-muted-foreground">Total Quizzes</p>
                    <p className="text-3xl font-bold">{data?.stats.totalQuizzes || 0}</p>
                  </div>
                </div>
              </CardContent>
            </Card>
          </div>

          <div className="grid grid-cols-1 lg:grid-cols-2 gap-8">
            {/* Recent Users */}
            <Card>
              <CardHeader className="pb-3">
                <div className="flex items-center justify-between">
                  <CardTitle className="text-lg">Recent Users</CardTitle>
                  <Button variant="ghost" size="sm" asChild>
                    <Link href="/admin/users">
                      View all
                      <ArrowRight className="ml-2 h-4 w-4" />
                    </Link>
                  </Button>
                </div>
              </CardHeader>
              <Separator />
              <CardContent className="pt-4">
                {!data?.recentUsers.length ? (
                  <div className="text-center py-8 text-muted-foreground">
                    No users yet.
                  </div>
                ) : (
                  <div className="space-y-3">
                    {data.recentUsers.map((user) => (
                      <div key={user.id} className="flex items-center justify-between p-3 rounded-lg bg-muted/50">
                        <div className="flex-grow min-w-0">
                          <p className="font-medium text-sm truncate">{user.username}</p>
                          <p className="text-xs text-muted-foreground truncate">{user.email}</p>
                        </div>
                        {user.isAdmin && (
                          <Badge variant="secondary">Admin</Badge>
                        )}
                      </div>
                    ))}
                  </div>
                )}
              </CardContent>
            </Card>

            {/* Recent Quiz Attempts */}
            <Card>
              <CardHeader className="pb-3">
                <CardTitle className="text-lg">Recent Quiz Attempts</CardTitle>
              </CardHeader>
              <Separator />
              <CardContent className="pt-4">
                {!data?.recentAttempts.length ? (
                  <div className="text-center py-8 text-muted-foreground">
                    No quiz attempts yet.
                  </div>
                ) : (
                  <div className="space-y-3">
                    {data.recentAttempts.map((attempt) => (
                      <div key={attempt.id} className="flex items-center gap-3 p-3 rounded-lg bg-muted/50">
                        <div className={`h-8 w-8 rounded-full flex items-center justify-center flex-shrink-0 ${
                          attempt.score >= 70 ? 'bg-emerald-500/20' : 'bg-destructive/20'
                        }`}>
                          <TrendingUp className={`h-4 w-4 ${
                            attempt.score >= 70 ? 'text-emerald-500' : 'text-destructive'
                          }`} />
                        </div>
                        <div className="flex-grow min-w-0">
                          <p className="font-medium text-sm truncate">{attempt.user.username}</p>
                          <p className="text-xs text-muted-foreground truncate">{attempt.quiz.title}</p>
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
        </div>
      </main>
    </div>
  );
}
