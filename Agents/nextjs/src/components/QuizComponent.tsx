'use client';

import { useState } from 'react';
import { useSession } from 'next-auth/react';
import { Button } from '@/components/ui/button';
import { Progress } from '@/components/ui/progress';
import { Card, CardContent } from '@/components/ui/card';
import { cn } from '@/lib/utils';
import { 
  ChevronLeft, 
  ChevronRight, 
  Send,
  RefreshCw,
  X,
  Loader2,
  Trophy,
  AlertCircle
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

interface QuizResult {
  score: number;
  correctAnswers: number;
  totalQuestions: number;
  percentage: string;
}

interface QuizComponentProps {
  quiz: Quiz;
  onClose: () => void;
}

export default function QuizComponent({ quiz, onClose }: QuizComponentProps) {
  const { data: session } = useSession();
  const [currentQuestion, setCurrentQuestion] = useState(0);
  const [answers, setAnswers] = useState<Record<number, number>>({});
  const [submitted, setSubmitted] = useState(false);
  const [result, setResult] = useState<QuizResult | null>(null);
  const [loading, setLoading] = useState(false);

  const question = quiz.questions[currentQuestion];
  const progressValue = ((currentQuestion + 1) / quiz.questions.length) * 100;

  const handleSelectOption = (optionId: number) => {
    if (submitted) return;
    setAnswers({ ...answers, [question.id]: optionId });
  };

  const handleNext = () => {
    if (currentQuestion < quiz.questions.length - 1) {
      setCurrentQuestion(currentQuestion + 1);
    }
  };

  const handlePrevious = () => {
    if (currentQuestion > 0) {
      setCurrentQuestion(currentQuestion - 1);
    }
  };

  const handleSubmit = async () => {
    if (!session) {
      alert('Please sign in to submit the quiz');
      return;
    }

    setLoading(true);
    try {
      const response = await fetch(`/api/quizzes/${quiz.id}/submit`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ answers }),
      });

      if (response.ok) {
        const data = await response.json();
        setResult(data);
        setSubmitted(true);
      }
    } catch (error) {
      console.error('Error submitting quiz:', error);
    } finally {
      setLoading(false);
    }
  };

  if (submitted && result) {
    const passed = result.score >= 70;
    
    return (
      <div className="space-y-6">
        <div className="text-center py-4">
          <div className={cn(
            "inline-flex items-center justify-center w-20 h-20 rounded-full mb-4",
            passed ? "bg-emerald-500/10" : "bg-destructive/10"
          )}>
            {passed ? (
              <Trophy className="h-10 w-10 text-emerald-500" />
            ) : (
              <AlertCircle className="h-10 w-10 text-destructive" />
            )}
          </div>
          <div className={cn(
            "text-5xl font-bold mb-2",
            passed ? "text-emerald-500" : "text-destructive"
          )}>
            {result.percentage}%
          </div>
          <p className="text-muted-foreground">
            You got <span className="font-semibold text-foreground">{result.correctAnswers}</span> out of <span className="font-semibold text-foreground">{result.totalQuestions}</span> questions correct
          </p>
          {passed ? (
            <p className="text-emerald-600 mt-2 font-medium">🎉 Great job! You passed the quiz!</p>
          ) : (
            <p className="text-destructive mt-2 font-medium">Keep practicing! You can try again.</p>
          )}
        </div>
        <div className="flex justify-center gap-3">
          <Button
            onClick={() => {
              setSubmitted(false);
              setResult(null);
              setAnswers({});
              setCurrentQuestion(0);
            }}
          >
            <RefreshCw className="h-4 w-4 mr-2" />
            Try Again
          </Button>
          <Button variant="outline" onClick={onClose}>
            Close
          </Button>
        </div>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      {/* Progress */}
      <div className="space-y-2">
        <div className="flex items-center justify-between text-sm">
          <span className="text-muted-foreground">
            Question {currentQuestion + 1} of {quiz.questions.length}
          </span>
          <span className="text-muted-foreground font-medium">
            {Math.round(progressValue)}%
          </span>
        </div>
        <Progress value={progressValue} className="h-2" />
      </div>

      {/* Question */}
      <div>
        <h3 className="text-lg font-medium mb-4">
          {question.questionText}
        </h3>
        <div className="space-y-3">
          {question.options.map((option) => {
            const isSelected = answers[question.id] === option.id;
            return (
              <button
                key={option.id}
                onClick={() => handleSelectOption(option.id)}
                className={cn(
                  "w-full text-left p-4 rounded-lg border-2 transition-all",
                  isSelected
                    ? "border-primary bg-primary/5"
                    : "border-border hover:border-primary/50 hover:bg-muted/50"
                )}
              >
                <div className="flex items-center gap-3">
                  <div className={cn(
                    "w-5 h-5 rounded-full border-2 flex items-center justify-center transition-colors",
                    isSelected 
                      ? "border-primary bg-primary" 
                      : "border-muted-foreground/30"
                  )}>
                    {isSelected && (
                      <div className="w-2 h-2 bg-white rounded-full" />
                    )}
                  </div>
                  <span className={cn(
                    "text-sm",
                    isSelected ? "text-foreground font-medium" : "text-muted-foreground"
                  )}>
                    {option.optionText}
                  </span>
                </div>
              </button>
            );
          })}
        </div>
      </div>

      {/* Navigation */}
      <div className="flex justify-between items-center pt-4">
        <Button
          variant="ghost"
          onClick={handlePrevious}
          disabled={currentQuestion === 0}
        >
          <ChevronLeft className="h-4 w-4 mr-1" />
          Previous
        </Button>

        {currentQuestion === quiz.questions.length - 1 ? (
          <Button
            onClick={handleSubmit}
            disabled={loading || Object.keys(answers).length !== quiz.questions.length}
            className="bg-emerald-600 hover:bg-emerald-700"
          >
            {loading ? (
              <>
                <Loader2 className="h-4 w-4 mr-2 animate-spin" />
                Submitting...
              </>
            ) : (
              <>
                <Send className="h-4 w-4 mr-2" />
                Submit Quiz
              </>
            )}
          </Button>
        ) : (
          <Button
            onClick={handleNext}
            disabled={!answers[question.id]}
          >
            Next
            <ChevronRight className="h-4 w-4 ml-1" />
          </Button>
        )}
      </div>

      <Button
        variant="ghost"
        onClick={onClose}
        className="w-full text-muted-foreground hover:text-foreground"
      >
        <X className="h-4 w-4 mr-2" />
        Cancel Quiz
      </Button>
    </div>
  );
}
