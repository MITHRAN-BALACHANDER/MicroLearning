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
    <div className="min-h-screen bg-gradient-to-br from-indigo-50 via-white to-cyan-50 flex items-center justify-center p-4">
      <div className="w-full max-w-2xl bg-white rounded-2xl shadow-2xl border border-gray-100 overflow-hidden">
        {/* Header */}
        <div className="bg-gradient-to-r from-indigo-600 to-purple-600 px-8 py-6">
          <h2 className="text-2xl font-bold text-white mb-2">We'd love your feedback!</h2>
          <p className="text-indigo-100 text-sm">Help us improve by sharing your thoughts</p>
        </div>
        
        {/* Content */}
        <div className="p-8 space-y-6">
          {/* Feedback Textarea */}
          <div className="space-y-2">
            <label className="block text-sm font-semibold text-gray-700">Your Feedback</label>
            <textarea
              className="w-full p-4 border-2 border-gray-200 rounded-xl text-sm resize-none focus:border-indigo-500 focus:ring-2 focus:ring-indigo-200 transition-all duration-200 placeholder-gray-400"
              rows="6"
              placeholder="Share your thoughts, suggestions, or experiences with us..."
              value={feedback}
              onChange={(e) => setFeedback(e.target.value)}
            />
          </div>
          
          {/* Submit Button */}
          <div className="flex justify-end pt-2">
            <button 
              className="bg-gradient-to-r from-indigo-600 to-purple-600 text-white px-8 py-3 rounded-xl font-semibold hover:from-indigo-700 hover:to-purple-700 transform hover:scale-105 transition-all duration-200 shadow-lg hover:shadow-xl"
              onClick={handleSubmit}
            >
              Send Feedback
            </button>
          </div>
          
          {/* Success Message */}
          {submitted && (
            <div className="bg-green-50 border border-green-200 rounded-xl p-4 flex items-center gap-3">
              <div className="w-6 h-6 bg-green-500 rounded-full flex items-center justify-center">
                <span className="text-white text-sm font-bold">✓</span>
              </div>
              <p className="text-green-800 font-medium">Thank you for your valuable feedback!</p>
            </div>
          )}
        </div>
      </div>
    </div>
  );
};

export default Feedback;