import React, { useState } from 'react';
import { User, ThumbsUp } from 'lucide-react';

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
    <div className="p-8 m-5">
      <div className="flex justify-between items-center mb-6">
        <div className="flex items-center gap-2">
          <ThumbsUp size={24} className="text-black" />
          <h2 className="text-xl font-semibold">Feedbacks by user</h2>
        </div>
       
      </div>

      
      <div className="grid grid-cols-1 sm:grid-cols-2 md:grid-cols-4 gap-4">
        {feedbacks.map((fb, index) => (
          <div
            key={index}
            className="bg-gray-100 p-4 rounded shadow-sm min-h-[100px]"
          >
            <div className="flex justify-between items-center text-sm font-medium text-gray-700 mb-2">
              <span>{fb.name}</span>
              <User size={16} className="text-gray-600" />
            </div>
            <p className="text-gray-800 text-sm">{fb.message}</p>
          </div>
        ))}
      </div>

      {/* Feedback Textarea */}
      <div className="mt-10 border-2 border-gray-200 rounded-xl p-4">
        <textarea
          rows={3}
          value={newFeedback}
          onChange={(e) => setNewFeedback(e.target.value)}
          placeholder="Love our platform! Share your views....."
          className="w-full p-2 text-gray-800 text-sm rounded outline-none"
        />
        <div className="flex justify-end mt-2">
          <button
            onClick={handleSendFeedback}
            className="bg-blue-600 text-white px-4 py-2 text-sm rounded hover:bg-blue-700 transition"
          >
            Send us a feedback
          </button>
        </div>
      </div>
    </div>
  );
};

export default FeedbackDisplay;
