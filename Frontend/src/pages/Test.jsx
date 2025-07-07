import React, { useState } from 'react';

const Test = () => {
  const [answers, setAnswers] = useState({});
  const [submitted, setSubmitted] = useState(false);
  const [score, setScore] = useState(0);
 const [zero, setZero] = useState(false);

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

  return (
    <div className="max-w-2xl mx-auto p-4 h-screen flex flex-col">
      <h1 className="text-2xl font-bold mb-4">Dummy Test</h1>

      <div className="flex-1 overflow-y-scroll space-y-6 border p-4 rounded-md bg-gray-50">
        {dummyQuestions.map((q) => (
          <div key={q.id} className="bg-white p-4 rounded shadow">
            <p className="font-medium mb-2">
              {q.id}. {q.question}
            </p>
            <div className="space-y-1">
              {q.options.map((option, idx) => {
                const isCorrect = submitted && option === q.correct;
                const isWrongSelected =
                  submitted && option === answers[q.id] && option !== q.correct;

                return (
                  <label key={idx} className="block">
                    <input
                      type="radio"
                      name={`q-${q.id}`}
                      value={option}
                      disabled={submitted}
                      checked={answers[q.id] === option}
                      onChange={() => handleChange(q.id, option)}
                      className="mr-2"
                    />
                    <span
                      className={`${
                        isCorrect
                          ? 'text-green-600 font-semibold'
                          : isWrongSelected
                          ? 'text-red-600 line-through'
                          : ''
                      }`}
                    >
                      {option}
                    </span>
                  </label>
                );
              })}
            </div>
            {submitted && (
              <p className="text-sm mt-2 text-gray-500">
                Correct Answer: <span className="font-semibold">{q.correct}</span>
              </p>
            )}
          </div>
        ))}
      </div>

      <div className="mt-4 text-right">
        {!submitted ? (
          <button
            className="bg-blue-600 text-white px-5 py-2 rounded hover:bg-blue-600"
            onClick={handleSubmit}
          >
            Submit
          </button>
          
        ) : (
          <div className="text-lg font-semibold text-green-700">
            Your Score: {score} / {dummyQuestions.length}
          </div>
        )}
       { zero && (
          <div className="text-lg font-semibold text-red-700">
            You have not answered any questions correctly.
          </div>
        )}
      </div>
    </div>
  );
};

export default Test;
