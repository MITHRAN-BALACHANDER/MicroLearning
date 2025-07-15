import React, { useState } from 'react';
import { User, ThumbsUp, Send, MessageCircle } from 'lucide-react';

const FeedbackDisplay = () => {
  const [feedbacks, setFeedbacks] = useState([
    { name: 'sahana', message: 'Thank you for good explanation!' },
    { name: 'sahana', message: 'Thank you for good explanation!' },
    { name: 'sahana', message: 'Thank you for good explanation!' },
    { name: 'sahana', message: 'Thank you for good explanation!' },
    { name: 'sahana', message: 'Thank you for good explanation!' },
    { name: 'sahana', message: 'Thank you for good explanation!' },
    { name: 'sahana', message: 'Thank you for good explanation!' },
    { name: 'sahana', message: 'Thank you for good explanation!' },
    { name: 'sahana', message: 'Thank you for good explanation!' },
  ]);

  const [newFeedback, setNewFeedback] = useState('');

  const handleSendFeedback = () => {
    if (newFeedback.trim()) {
      setFeedbacks([...feedbacks, { name: 'You', message: newFeedback }]);
      setNewFeedback('');
    }
  };

  return (
    <div className="min-h-screen bg-slate-50 p-6">
      <div className="max-w-7xl mx-auto">


        <div className="bg-white rounded-2xl shadow-sm border border-slate-200 p-6 mb-8">
          <div className="flex items-center gap-3">
            <div className="p-2 bg-blue-50 rounded-xl">
              <MessageCircle size={24} className="text-blue-600" />
            </div>
            <div>
              <h1 className="text-2xl font-bold text-slate-900">User Feedback</h1>
              <p className="text-slate-600 text-sm mt-1">See what our users are saying about the platform</p>
            </div>
          </div>
        </div>

        {/* Feedback Grid */}
        <div className="grid grid-cols-1 sm:grid-cols-2 md:grid-cols-3 lg:grid-cols-4 xl:grid-cols-5 gap-4 mb-8">
          {feedbacks.map((fb, index) => (
            <div
              key={index}
              className="bg-white rounded-xl border border-slate-200 p-5 hover:shadow-md transition-all duration-200 hover:border-slate-300"
            >
              <div className="flex items-center justify-between mb-3">
                <div className="flex items-center gap-2">
                  <div className="w-8 h-8 bg-blue-100 rounded-full flex items-center justify-center">
                    <User size={14} className="text-blue-600" />
                  </div>
                  <span className="text-sm font-semibold text-slate-700">{fb.name}</span>
                </div>
               
              </div>
              <p className="text-slate-600 text-sm leading-relaxed">{fb.message}</p>
            </div>
          ))}
        </div>


        <div className="bg-white rounded-2xl shadow-sm border border-slate-200 p-6">
          <div className="flex items-center gap-3 mb-4">
            <div className="p-2 bg-emerald-50 rounded-xl">
              <Send size={20} className="text-emerald-600" />
            </div>
            <h2 className="text-lg font-semibold text-slate-900">Share Your Feedback</h2>
          </div>
          
          <div className="space-y-4">
            <textarea
              rows={4}
              value={newFeedback}
              onChange={(e) => setNewFeedback(e.target.value)}
              placeholder="Love our platform! Share your views....."
              className="w-full p-4 text-slate-700 bg-slate-50 border border-slate-200 rounded-xl resize-none focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent transition-all duration-200"
            />
            
            <div className="flex justify-end">
              <button
                onClick={handleSendFeedback}
                disabled={!newFeedback.trim()}
                className="flex items-center gap-2 bg-blue-600 text-white px-6 py-3 rounded-xl hover:bg-blue-700 disabled:bg-slate-300 disabled:cursor-not-allowed transition-all duration-200 font-medium"
              >
                <Send size={16} />
                Send Feedback
              </button>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};

export default FeedbackDisplay;