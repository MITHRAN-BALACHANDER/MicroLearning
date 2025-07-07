import React from 'react';
import { useNavigate } from 'react-router-dom';
const NotFoundPage = () => {
    const navigate=useNavigate();
  return (
    <div className="h-screen flex flex-col items-center justify-center bg-white font-sans">
      <h1
        className="text-[8rem] font-bold text-gray-800 transition duration-300 ease-in-out hover:text-shadow-lg hover:text-black/80 cursor-pointer"
        style={{
          transition: 'text-shadow 0.3s ease-in-out',
        }}
        onMouseEnter={(e) => {
          e.currentTarget.style.textShadow = '0 0 20px rgba(0,0,0,0.5)';
        }}
        onMouseLeave={(e) => {
          e.currentTarget.style.textShadow = 'none';
        }}
      >
        404
      </h1>
      <h2 className="text-xl text-gray-600 mt-4">PAGE NOT FOUND</h2>
      <p className="text-sm text-gray-400 mt-2">Oops! We lost this page in the multiverse.</p>
      <button 
      className='bg-gray-100 m-3 p-2 rounded cursor-pointer hover:bg-gray-300 transition-all'
      onClick={()=>navigate('/')}>Head to home page </button>
    </div>
  );
};

export default NotFoundPage;
