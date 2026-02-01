'use client';

import { useState } from 'react';
import { useSession } from 'next-auth/react';
import Link from 'next/link';
import QuizComponent from './QuizComponent';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { Separator } from '@/components/ui/separator';
import { 
  CheckCircle2, 
  ChevronLeft, 
  ChevronRight,
  ClipboardList,
  Loader2,
  Play
} from 'lucide-react';

interface Option {
  id: number;
  optionText: string;
  isCorrect: boolean;
}

interface Question {
  id: number;
  questionText: string;
  questionType: string;
  options: Option[];
}

interface Quiz {
  id: number;
  title: string;
  questions: Question[];
}

interface Lesson {
  id: number;
  title: string;
  content: string;
  quizzes: Quiz[];
}

interface AdjacentLesson {
  id: number;
  title: string;
}

interface LessonContentProps {
  lesson: Lesson;
  courseId: number;
  previousLesson: AdjacentLesson | null;
  nextLesson: AdjacentLesson | null;
}

export default function LessonContent({
  lesson,
  courseId,
  previousLesson,
  nextLesson,
}: LessonContentProps) {
  const { data: session } = useSession();
  const [completed, setCompleted] = useState(false);
  const [marking, setMarking] = useState(false);
  const [activeQuizId, setActiveQuizId] = useState<number | null>(null);

  const handleMarkComplete = async () => {
    if (!session) return;
    
    setMarking(true);
    try {
      const response = await fetch('/api/progress', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          lessonId: lesson.id,
          courseId: courseId,
        }),
      });
      
      if (response.ok) {
        setCompleted(true);
      }
    } catch (error) {
      console.error('Error marking lesson complete:', error);
    } finally {
      setMarking(false);
    }
  };

  return (
    <div className="space-y-8">
      {/* Main Content Card */}
      <Card>
        <CardHeader>
          <CardTitle className="text-2xl md:text-3xl">{lesson.title}</CardTitle>
        </CardHeader>
        <Separator />
        <CardContent className="pt-6">
          <div 
            className="prose prose-slate dark:prose-invert max-w-none
              prose-headings:font-semibold prose-headings:text-foreground
              prose-p:text-muted-foreground prose-p:leading-relaxed
              prose-a:text-primary prose-a:no-underline hover:prose-a:underline
              prose-strong:text-foreground
              prose-code:text-primary prose-code:bg-muted prose-code:px-1.5 prose-code:py-0.5 prose-code:rounded
              prose-pre:bg-muted prose-pre:border prose-pre:border-border
              prose-ul:text-muted-foreground prose-ol:text-muted-foreground
              prose-li:marker:text-muted-foreground"
            dangerouslySetInnerHTML={{ __html: lesson.content }}
          />

          {/* Mark Complete Button */}
          {session && !completed && (
            <div className="mt-8 pt-6 border-t border-border">
              <Button
                onClick={handleMarkComplete}
                disabled={marking}
                className="bg-emerald-600 hover:bg-emerald-700"
              >
                {marking ? (
                  <>
                    <Loader2 className="h-4 w-4 mr-2 animate-spin" />
                    Marking...
                  </>
                ) : (
                  <>
                    <CheckCircle2 className="h-4 w-4 mr-2" />
                    Mark as Complete
                  </>
                )}
              </Button>
            </div>
          )}

          {completed && (
            <div className="mt-8 pt-6 border-t border-border">
              <div className="bg-emerald-500/10 text-emerald-700 dark:text-emerald-400 px-4 py-3 rounded-lg flex items-center">
                <CheckCircle2 className="h-5 w-5 mr-2" />
                Lesson completed!
              </div>
            </div>
          )}
        </CardContent>
      </Card>

      {/* Quizzes */}
      {lesson.quizzes.length > 0 && (
        <Card>
          <CardHeader className="pb-3">
            <div className="flex items-center gap-2">
              <ClipboardList className="h-5 w-5 text-primary" />
              <CardTitle>Test Your Knowledge</CardTitle>
            </div>
          </CardHeader>
          <Separator />
          <CardContent className="pt-0">
            <div className="divide-y divide-border">
              {lesson.quizzes.map((quiz) => (
                <div key={quiz.id} className="py-6 first:pt-6 last:pb-0">
                  {activeQuizId === quiz.id ? (
                    <QuizComponent 
                      quiz={quiz} 
                      onClose={() => setActiveQuizId(null)} 
                    />
                  ) : (
                    <div className="flex items-center justify-between">
                      <div>
                        <h3 className="font-medium">{quiz.title}</h3>
                        <p className="text-sm text-muted-foreground">
                          {quiz.questions.length} question{quiz.questions.length !== 1 ? 's' : ''}
                        </p>
                      </div>
                      <Button onClick={() => setActiveQuizId(quiz.id)}>
                        <Play className="h-4 w-4 mr-2" />
                        Start Quiz
                      </Button>
                    </div>
                  )}
                </div>
              ))}
            </div>
          </CardContent>
        </Card>
      )}

      {/* Navigation */}
      <div className="flex justify-between items-center">
        {previousLesson ? (
          <Button variant="ghost" asChild>
            <Link href={`/courses/${courseId}/lessons/${previousLesson.id}`}>
              <ChevronLeft className="h-4 w-4 mr-2" />
              <span className="hidden sm:inline">Previous:</span> {previousLesson.title}
            </Link>
          </Button>
        ) : (
          <div />
        )}
        
        {nextLesson ? (
          <Button variant="ghost" asChild>
            <Link href={`/courses/${courseId}/lessons/${nextLesson.id}`}>
              <span className="hidden sm:inline">Next:</span> {nextLesson.title}
              <ChevronRight className="h-4 w-4 ml-2" />
            </Link>
          </Button>
        ) : (
          <Button variant="ghost" asChild>
            <Link href={`/courses/${courseId}`}>
              Back to Course
              <ChevronRight className="h-4 w-4 ml-2" />
            </Link>
          </Button>
        )}
      </div>
    </div>
  );
}
