import { useParams } from 'react-router-dom';

const allVideos = [
  {
    id: 'budgeting101',
    title: 'Art of Budgeting',
    src: '/videos/sample.mp4',
    description: 'Learn how to manage your finances.',
    suggestion: 'Write down monthly expenses.',
  },
  {
    id: 'invest101',
    title: 'Investing Basics',
    src: '/videos/sample.mp4',
    description: 'Start your investment journey.',
    suggestion: 'Start with mutual funds or SIPs.',
  },
  {
    id: 'startup101',
    title: 'Starting a Startup',
    src: '/videos/sample.mp4',
    description: 'Steps to launch your startup.',
    suggestion: 'Validate your idea before building.',
  },
];

const Content = () => {
  const { videoID } = useParams();
  const video = allVideos.find(v => v.id === videoID);

  if (!video) {
    return <div className="p-10 text-red-500">⚠️ Video not found.</div>;
  }

  return (
    <div className="flex flex-col h-screen">
      <div className="w-[99%] m-2 mt-20 h-[50vh] overflow-hidden flex flex-wrap items-center">
        <video
          className="w-full h-full object-cover"
          src={video.src}
          controls
          autoPlay
          muted
          loop
        />
      </div>

      <div className="flex flex-wrap justify-between mr-5">
        <div className="ml-7">
          <h1 className="text-3xl font-bold">{video.title}</h1>
          <p>{video.description}</p>
          <p className="text-sm italic text-gray-500">{video.suggestion}</p>
        </div>
        <div>
          <button
            onClick={() => console.log('Test Review')}
            
            className="bg-gray-200 rounded-2xl  hover:text-white px-4 py-2 m-2 hover:bg-gray-700 transition duration-400 cursor-pointer"
          >
            Test Review
          </button>
          <button
            onClick={() => console.log('Feedback')}
            className="bg-gray-200 rounded-2xl hover:text-white px-4 py-2 m-2 hover:bg-gray-700 transition duration-300 cursor-pointer"
          >
            Feedback
          </button>
        </div>
      </div>
    </div>
  );
};

export default Content;
