import React, { useState } from 'react';
const Content
 = () => {
const [video,setVideo]= useState(null);
const [videoName,setVideoName]= useState("Sample Video");
const [videoDescription,setVideoDescription]= useState("This is a sample video description.");
const [suggestion,setSuggestion]= useState("This is a sample suggestion for the video.");
const handleTest=()=>{
    
    console.log("Test button clicked");
}
  return (
    <div className="flex flex-col  h-screen ">
    <div className="w-[99%] m-2 mt-20 h-[50vh] overflow-hidden flex flex-wrap items-center">
      <video
        className="w-full h-full object-cover"
        src="/videos/sample.mp4"
        controls
        autoPlay
        muted
        loop
      >
      
      </video>
      
    </div>
    <div className='flex flex-wrap justify-between mr-5'>
    <div className='ml-7'>
       <h1 className='text-3xl poppins-semibold'>{videoName}</h1>
       <p className='poppins-regular'>{videoDescription}</p>
      </div>
      <div>
        <button onClick={handleTest}
        className='bg-gray-200 rounded-2xl hover:text-white px-4 py-2 m-2 hover:bg-gray-700 transition duration-300 cursor-pointer' >
            Test Review
        </button>
        <button className='bg-gray-200 rounded-2xl hover:text-white px-4 py-2 m-2 hover:bg-gray-700 transition duration-300 cursor-pointer'>
            Feedback
        </button>
      </div>
      </div>
    </div>
  );
};

export default Content
;
