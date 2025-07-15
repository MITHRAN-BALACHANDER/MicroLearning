import React, { useState } from 'react';
import { CheckCircle, XCircle, Clock, Award, FileText, ChevronLeft, ChevronRight } from 'lucide-react';

const Test = () => {
  const [answers, setAnswers] = useState({});
  const [submitted, setSubmitted] = useState(false);
  const [score, setScore] = useState(0);
  const [zero, setZero] = useState(false);
  const [currentQuestion, setCurrentQuestion] = useState(0);

  const dummyQuestions = [
    {
      id: 1,
      question: "Dummy Question 1",
      options: ["Option A", "Option B", "Option C", "Option D"],
      correct: "Option B",
    },
    {
      id: 2,
      question: "Dummy Question 2",
      options: ["Option A", "Option B", "Option C", "Option D"],
      correct: "Option C",
    },
    {
      id: 3,
      question: "Dummy Question 3",
      options: ["Option A", "Option B", "Option C", "Option D"],
      correct: "Option D",
    },
    {
      id: 4,
      question: "Dummy Question 4",
      options: ["Option A", "Option B", "Option C", "Option D"],
      correct: "Option A",
    },
    {
      id: 5,
      question: "Dummy Question 5",
      options: ["Option A", "Option B", "Option C", "Option D"],
      correct: "Option C",
    },
  ];

  const handleChange = (questionId, selectedOption) => {
    setAnswers((prev) => ({ ...prev, [questionId]: selectedOption }));
  };

  const handleSubmit = () => {
    let tempScore = 0;
    if(tempScore > 0) {
     setScore(tempScore);
      setSubmitted(true);
      return;
    }
    if(Object.keys(answers).length === 0) {
      setZero(true);
      return;
    }
    setZero(false);
    setSubmitted(true);
    setScore(tempScore);
    dummyQuestions.forEach((q) => {
      if (answers[q.id] === q.correct) {
        tempScore++;
      }
    });
  };

  const goToNext = () => {
    if (currentQuestion < dummyQuestions.length - 1) {
      setCurrentQuestion(currentQuestion + 1);
    }
  };

  const goToPrev = () => {
    if (currentQuestion > 0) {
      setCurrentQuestion(currentQuestion - 1);
    }
  };

  const goToQuestion = (index) => {
    setCurrentQuestion(index);
  };

  const getScoreColor = () => {
    const percentage = (score / dummyQuestions.length) * 100;
    if (percentage >= 80) return 'text-emerald-600';
    if (percentage >= 60) return 'text-yellow-600';
    return 'text-red-600';
  };

  const currentQ = dummyQuestions[currentQuestion];

  return (
    <div className="min-h-screen bg-slate-50 p-6">
      <div className="max-w-4xl mx-auto">
       
        <div className="bg-white rounded-2xl shadow-sm border border-slate-200 p-6 mb-6">
          <div className="flex items-center gap-3">
            <div className="p-2 bg-blue-50 rounded-xl">
              <FileText size={24} className="text-blue-600" />
            </div>
            <div className="flex-1">
              <h1 className="text-2xl font-bold text-slate-900">Dummy Test</h1>
              <p className="text-slate-600 text-sm mt-1">
                Answer all questions and click submit to see your results
              </p>
            </div>
            {!submitted && (
              <div className="flex items-center gap-2 text-slate-600">
                <Clock size={16} />
                <span className="text-sm">In Progress</span>
              </div>
            )}
          </div>
        </div>

        
        <div className="bg-white rounded-2xl shadow-sm border border-slate-200 p-6 mb-6">
          <div className="flex items-center justify-between mb-4">
            <h3 className="text-lg font-semibold text-slate-900">Progress</h3>
            <span className="text-sm text-slate-600">
              Question {currentQuestion + 1} of {dummyQuestions.length}
            </span>
          </div>
          
          <div className="w-full bg-slate-200 rounded-full h-2 mb-4">
            <div 
              className="bg-blue-600 h-2 rounded-full transition-all duration-300"
              style={{ width: `${((currentQuestion + 1) / dummyQuestions.length) * 100}%` }}
            ></div>
          </div>

          {/* Question Navigation Pills */}
          <div className="flex flex-wrap gap-2">
            {dummyQuestions.map((_, index) => (
              <button
                key={index}
                onClick={() => goToQuestion(index)}
                className={`w-8 h-8 rounded-full text-sm font-medium transition-all duration-200 ${
                  index === currentQuestion
                    ? 'bg-blue-600 text-white'
                    : answers[dummyQuestions[index].id]
                    ? 'bg-emerald-100 text-emerald-700 hover:bg-emerald-200'
                    : 'bg-slate-200 text-slate-600 hover:bg-slate-300'
                }`}
              >
                {index + 1}
              </button>
            ))}
          </div>
        </div>

      
        <div className="bg-white rounded-2xl shadow-sm border border-slate-200 mb-6">
          <div className="p-6 border-b border-slate-100">
            <div className="flex items-center gap-3">
              <div className="w-10 h-10 bg-blue-100 rounded-full flex items-center justify-center">
                <span className="text-blue-600 font-semibold">{currentQ.id}</span>
              </div>
              <h2 className="text-xl font-semibold text-slate-900">{currentQ.question}</h2>
            </div>
          </div>
          
          <div className="p-6">
            <div className="space-y-3">
              {currentQ.options.map((option, idx) => {
                const isCorrect = submitted && option === currentQ.correct;
                const isWrongSelected =
                  submitted && option === answers[currentQ.id] && option !== currentQ.correct;

                return (
                  <label 
                    key={idx} 
                    className={`flex items-center gap-3 p-4 rounded-xl border cursor-pointer transition-all duration-200 ${
                      submitted ? 'cursor-not-allowed' : 'hover:bg-blue-50 hover:border-blue-200'
                    } ${
                      isCorrect 
                        ? 'bg-emerald-50 border-emerald-200' 
                        : isWrongSelected 
                        ? 'bg-red-50 border-red-200' 
                        : answers[currentQ.id] === option && !submitted
                        ? 'bg-blue-50 border-blue-200'
                        : 'bg-white border-slate-200'
                    }`}
                  >
                    <input
                      type="radio"
                      name={`q-${currentQ.id}`}
                      value={option}
                      disabled={submitted}
                      checked={answers[currentQ.id] === option}
                      onChange={() => handleChange(currentQ.id, option)}
                      className="w-4 h-4 text-blue-600 border-gray-300 focus:ring-blue-500 focus:ring-2"
                    />
                    <span
                      className={`flex-1 ${
                        isCorrect
                          ? 'text-emerald-700 font-semibold'
                          : isWrongSelected
                          ? 'text-red-700 line-through'
                          : 'text-slate-700'
                      }`}
                    >
                      {option}
                    </span>
                    {isCorrect && <CheckCircle size={20} className="text-emerald-600" />}
                    {isWrongSelected && <XCircle size={20} className="text-red-600" />}
                  </label>
                );
              })}
            </div>
            
            {submitted && (
              <div className="mt-4 p-4 bg-blue-50 rounded-xl border border-blue-200">
                <p className="text-sm text-blue-700">
                  <span className="font-medium">Correct Answer:</span> {currentQ.correct}
                </p>
              </div>
            )}
          </div>
        </div>

        
        <div className="bg-white rounded-2xl shadow-sm border border-slate-200 p-6 mb-6">
          <div className="flex items-center justify-between">
            <button
              onClick={goToPrev}
              disabled={currentQuestion === 0}
              className="flex items-center gap-2 px-4 py-2 bg-slate-100 text-slate-700 rounded-xl hover:bg-slate-200 disabled:opacity-50 disabled:cursor-not-allowed transition-colors duration-200"
            >
              <ChevronLeft size={16} />
              Previous
            </button>
            
            <span className="text-sm text-slate-600">
              {currentQuestion + 1} / {dummyQuestions.length}
            </span>
            
            <button
              onClick={goToNext}
              disabled={currentQuestion === dummyQuestions.length - 1}
              className="flex items-center gap-2 px-4 py-2 bg-slate-100 text-slate-700 rounded-xl hover:bg-slate-200 disabled:opacity-50 disabled:cursor-not-allowed transition-colors duration-200"
            >
              Next
              <ChevronRight size={16} />
            </button>
          </div>
        </div>

        
        <div className="bg-white rounded-2xl shadow-sm border border-slate-200 p-6">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-3">
              <div className="p-2 bg-purple-50 rounded-xl">
                <Award size={20} className="text-purple-600" />
              </div>
              <h3 className="text-lg font-semibold text-slate-900">Test Results</h3>
            </div>
            
            <div className="text-right">
              {!submitted ? (
                <button
                  className="bg-blue-600 text-white px-6 py-3 rounded-xl hover:bg-blue-700 transition-colors duration-200 font-medium shadow-sm"
                  onClick={handleSubmit}
                >
                  Submit Test
                </button>
              ) : (
                <div className={`text-xl font-bold ${getScoreColor()}`}>
                  Your Score: {score} / {dummyQuestions.length}
                </div>
              )}
            </div>
          </div>
          
          {zero && (
            <div className="mt-4 p-4 bg-red-50 border border-red-200 rounded-xl">
              <div className="flex items-center gap-2">
                <XCircle size={16} className="text-red-600" />
                <span className="text-red-700 font-semibold">
                  You have not answered any questions correctly.
                </span>
              </div>
            </div>
          )}
        </div>
      </div>
    </div>
  );
};

export default Test;