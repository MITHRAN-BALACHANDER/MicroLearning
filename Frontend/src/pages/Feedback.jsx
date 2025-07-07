import React from 'react'
import { useState } from 'react';
import { useEffect } from 'react';
const Feedback = () => {
  const [feedback, setFeedback] = useState('');
  const [rating, setRating] = useState(0);
  const [submitted, setSubmitted] = useState(false);

  const handleSubmit = () => {
    const feedbackData = {
      feedback,
      rating,
      timestamp: new Date().toISOString(),
    };
    console.log('Feedback submitted:', feedbackData);
    setSubmitted(true);
    //api call to send feedbackData to the server will be added here
    
    
  };

  return (
<div className="flex items-center justify-center min-h-screen bg-white">
    <div className="w-[600px] bg-gray-200 p-6 rounded-md shadow-sm">
      <textarea
        className="w-full p-4 border-[.2px] rounded-md text-sm"
        rows="5"
        placeholder="Share your feedback here.."
        value={feedback}
        onChange={(e) => setFeedback(e.target.value)}
      />

     
      <div className="flex items-center gap-2 mt-4 bg-gray-400 p-2 rounded-md w-fit">
        {[1, 2, 3, 4, 5].map((star) => (
          <span
            key={star}
            className={`cursor-pointer text-xl ${
              star <= rating ? 'text-yellow-400' : 'text-black'
            }`}
            onClick={() => setRating(star)}
          >
            ★
          </span>
        ))}
      </div>

      <div className="mt-4 text-right">
        <button 
          className="bg-blue-600 text-white px-5 py-2 rounded-md hover:bg-blue-700"
          onClick={handleSubmit}
        >
          Send
        </button>
      </div>

      
      {submitted && (
        <p className="mt-2 text-green-600 text-sm">Thank you for your feedback!</p>
      )}
    </div>
    </div>
  );
};

export default Feedback;

  