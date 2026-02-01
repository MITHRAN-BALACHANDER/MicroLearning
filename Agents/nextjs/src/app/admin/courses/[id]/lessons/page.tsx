'use client';

import { useEffect, useState, use } from 'react';
import { useSession } from 'next-auth/react';
import { useRouter } from 'next/navigation';
import Link from 'next/link';
import Navbar from '@/components/Navbar';
import { Card, CardContent } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Textarea } from '@/components/ui/textarea';
import { Label } from '@/components/ui/label';
import { Badge } from '@/components/ui/badge';
import { Skeleton } from '@/components/ui/skeleton';
import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
  DialogFooter,
} from '@/components/ui/dialog';
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from '@/components/ui/table';
import { 
  ArrowLeft, 
  Plus, 
  FileText, 
  Pencil, 
  Trash2,
  ClipboardList,
  Loader2
} from 'lucide-react';

interface Lesson {
  id: number;
  title: string;
  content: string;
  orderIndex: number;
  quizzes: { id: number }[];
}

export default function AdminLessonsPage({ params }: { params: Promise<{ id: string }> }) {
  const resolvedParams = use(params);
  const courseId = parseInt(resolvedParams.id);
  const { data: session, status } = useSession();
  const router = useRouter();
  const [lessons, setLessons] = useState<Lesson[]>([]);
  const [loading, setLoading] = useState(true);
  const [showForm, setShowForm] = useState(false);
  const [editingLesson, setEditingLesson] = useState<Lesson | null>(null);
  const [formData, setFormData] = useState({ title: '', content: '' });
  const [submitting, setSubmitting] = useState(false);

  useEffect(() => {
    if (status === 'unauthenticated') {
      router.push('/login');
    } else if (status === 'authenticated' && !session?.user?.isAdmin) {
      router.push('/dashboard');
    }
  }, [status, session, router]);

  useEffect(() => {
    if (session?.user?.isAdmin) {
      fetchLessons();
    }
  }, [session]);

  const fetchLessons = async () => {
    try {
      const response = await fetch(`/api/courses/${courseId}/lessons`);
      if (response.ok) {
        const data = await response.json();
        setLessons(data);
      }
    } catch (error) {
      console.error('Error fetching lessons:', error);
    } finally {
      setLoading(false);
    }
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setSubmitting(true);
    
    const url = editingLesson 
      ? `/api/courses/${courseId}/lessons/${editingLesson.id}` 
      : `/api/courses/${courseId}/lessons`;
    const method = editingLesson ? 'PUT' : 'POST';

    try {
      const response = await fetch(url, {
        method,
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(formData),
      });

      if (response.ok) {
        fetchLessons();
        setShowForm(false);
        setEditingLesson(null);
        setFormData({ title: '', content: '' });
      }
    } catch (error) {
      console.error('Error saving lesson:', error);
    } finally {
      setSubmitting(false);
    }
  };

  const handleEdit = (lesson: Lesson) => {
    setEditingLesson(lesson);
    setFormData({ title: lesson.title, content: lesson.content });
    setShowForm(true);
  };

  const handleDelete = async (lessonId: number) => {
    if (!confirm('Are you sure you want to delete this lesson?')) return;

    try {
      const response = await fetch(`/api/courses/${courseId}/lessons/${lessonId}`, {
        method: 'DELETE',
      });

      if (response.ok) {
        fetchLessons();
      }
    } catch (error) {
      console.error('Error deleting lesson:', error);
    }
  };

  if (status === 'loading' || loading) {
    return (
      <div className="min-h-screen flex flex-col">
        <Navbar />
        <main className="flex-grow bg-muted/30 py-8">
          <div className="container mx-auto px-4">
            <Skeleton className="h-6 w-40 mb-2" />
            <Skeleton className="h-10 w-64 mb-8" />
            <Skeleton className="h-96" />
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
              <Button variant="ghost" size="sm" asChild className="mb-2 -ml-3">
                <Link href="/admin/courses">
                  <ArrowLeft className="h-4 w-4 mr-2" />
                  Back to Courses
                </Link>
              </Button>
              <div className="flex items-center gap-2">
                <FileText className="h-6 w-6 text-primary" />
                <h1 className="text-3xl font-bold">Manage Lessons</h1>
              </div>
            </div>
            <Button
              onClick={() => {
                setShowForm(true);
                setEditingLesson(null);
                setFormData({ title: '', content: '' });
              }}
            >
              <Plus className="h-4 w-4 mr-2" />
              Add Lesson
            </Button>
          </div>

          {/* Lesson Form Dialog */}
          <Dialog open={showForm} onOpenChange={(open) => {
            if (!open) {
              setShowForm(false);
              setEditingLesson(null);
            }
          }}>
            <DialogContent className="sm:max-w-2xl max-h-[90vh] overflow-y-auto">
              <DialogHeader>
                <DialogTitle>
                  {editingLesson ? 'Edit Lesson' : 'Add New Lesson'}
                </DialogTitle>
              </DialogHeader>
              <form onSubmit={handleSubmit} className="space-y-4">
                <div className="space-y-2">
                  <Label htmlFor="title">Title</Label>
                  <Input
                    id="title"
                    value={formData.title}
                    onChange={(e) => setFormData({ ...formData, title: e.target.value })}
                    placeholder="Lesson title"
                    required
                  />
                </div>
                <div className="space-y-2">
                  <Label htmlFor="content">Content (HTML supported)</Label>
                  <Textarea
                    id="content"
                    value={formData.content}
                    onChange={(e) => setFormData({ ...formData, content: e.target.value })}
                    placeholder="Lesson content..."
                    rows={12}
                    className="font-mono text-sm"
                    required
                  />
                </div>
                <DialogFooter className="gap-2 sm:gap-0">
                  <Button
                    type="button"
                    variant="outline"
                    onClick={() => {
                      setShowForm(false);
                      setEditingLesson(null);
                    }}
                  >
                    Cancel
                  </Button>
                  <Button type="submit" disabled={submitting}>
                    {submitting && <Loader2 className="h-4 w-4 mr-2 animate-spin" />}
                    {editingLesson ? 'Update' : 'Create'}
                  </Button>
                </DialogFooter>
              </form>
            </DialogContent>
          </Dialog>

          {/* Lessons Table */}
          <Card>
            <CardContent className="p-0">
              <Table>
                <TableHeader>
                  <TableRow>
                    <TableHead className="w-20">Order</TableHead>
                    <TableHead>Title</TableHead>
                    <TableHead className="text-center">Quizzes</TableHead>
                    <TableHead className="text-right">Actions</TableHead>
                  </TableRow>
                </TableHeader>
                <TableBody>
                  {lessons.length === 0 ? (
                    <TableRow>
                      <TableCell colSpan={4} className="text-center py-12">
                        <FileText className="h-12 w-12 mx-auto text-muted-foreground mb-4" />
                        <p className="text-muted-foreground">No lessons found. Add your first lesson!</p>
                      </TableCell>
                    </TableRow>
                  ) : (
                    lessons.map((lesson) => (
                      <TableRow key={lesson.id}>
                        <TableCell>
                          <Badge variant="outline">{lesson.orderIndex + 1}</Badge>
                        </TableCell>
                        <TableCell className="font-medium">{lesson.title}</TableCell>
                        <TableCell className="text-center">
                          <Badge variant="secondary">{lesson.quizzes?.length || 0}</Badge>
                        </TableCell>
                        <TableCell className="text-right">
                          <div className="flex justify-end gap-2">
                            <Button variant="outline" size="sm" asChild>
                              <Link href={`/admin/courses/${courseId}/lessons/${lesson.id}/quizzes`}>
                                <ClipboardList className="h-4 w-4 mr-1" />
                                Quizzes
                              </Link>
                            </Button>
                            <Button
                              variant="ghost"
                              size="sm"
                              onClick={() => handleEdit(lesson)}
                            >
                              <Pencil className="h-4 w-4" />
                            </Button>
                            <Button
                              variant="ghost"
                              size="sm"
                              className="text-destructive hover:text-destructive"
                              onClick={() => handleDelete(lesson.id)}
                            >
                              <Trash2 className="h-4 w-4" />
                            </Button>
                          </div>
                        </TableCell>
                      </TableRow>
                    ))
                  )}
                </TableBody>
              </Table>
            </CardContent>
          </Card>
        </div>
      </main>
    </div>
  );
}
