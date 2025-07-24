import React from 'react';
import { Zap } from 'lucide-react';

const COLOR_CLASSES = {
  blue: 'bg-blue-400 hover:bg-blue-500 focus:ring-blue-400 text-blue-900',
  red: 'bg-red-400 hover:bg-red-500 focus:ring-red-400 text-red-900',
  green: 'bg-green-400 hover:bg-green-500 focus:ring-green-600 text-green-900',
  yellow: 'bg-yellow-400 hover:bg-yellow-500 focus:ring-yellow-400 text-yellow-900',
  purple: 'bg-purple-400 hover:bg-purple-500 focus:ring-purple-400 text-purple-900',
  gray: 'bg-gray-400 hover:bg-gray-500 focus:ring-gray-400 text-gray-900',
};

const Button = ({ onClick, text, color, Icon = Zap }) => {
  const colorClass = COLOR_CLASSES[color] || COLOR_CLASSES.blue;

  return (
    <button
      onClick={onClick}
      className={`inline-flex items-center px-4 py-2 rounded-xl font-bold shadow-lg
                  hover:shadow-xl focus:outline-none focus:ring-4 focus:ring-offset-1
                  transform active:scale-95 transition-all duration-300 ease-in-out ${colorClass}`}
    >
      {Icon && <Icon className="w-5 h-5 mr-2" />}
      <span className="text-base">{text}</span>
    </button>
  );
};

export default Button;
