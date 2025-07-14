import { useState } from 'react';
import { Disclosure } from '@headlessui/react';
import { ChevronDown } from 'lucide-react';
import { useNavigate } from 'react-router-dom';
const categories = [
  {
    name: 'Finance',
    videos: [
      {
        id: 'budgeting101',
        title: 'Art of Budgeting',
        learners: 3,
        rating: 4,
        src: '/videos/sample.mp4',
        description: 'Learn to manage your budget effectively.',
        suggestion: 'Try writing down your monthly expenses.'
      },
      {
        id: 'invest101',
        title: 'Investing Basics',
        learners: 5,
        rating: 5,
        src: '/videos/sample.mp4',
        description: 'Start investing with confidence.',
        suggestion: 'Look into index funds.'
      },
    ]
  },
  {
    name: 'Business',
    videos: [
      {
        id: 'startup101',
        title: 'Starting a Startup',
        learners: 4,
        rating: 4,
        src: '/videos/sample.mp4',
        description: 'Steps to launch your startup.',
        suggestion: 'Validate your idea before building.'
      }
    ]
  },
  { name: 'Banking', videos: [] },
  { name: 'Marketing', videos: [] },
  { name: 'Estimation', videos: [] },
];

export default function ContentDisplay() {
  const navigate = useNavigate();

  const handleCardClick = (video) => {
    navigate(`/content-management/${video.id}`);
  };
const [selectedVideo, setSelectedVideo] = useState(null);

  return (
    <div className="mx-auto p-4 mt-20 max-w-7xl">
     
      {selectedVideo && (
        <div className="mb-10">
          <div className="w-full h-[50vh] overflow-hidden rounded-xl shadow">
            <video
              className="w-full h-full object-cover"
              src={selectedVideo.src}
              controls
              autoPlay
              muted
              loop
            />
          </div>

          <div className="flex flex-wrap justify-between items-start mt-4">
            <div>
              <h1 className="text-3xl font-bold">{selectedVideo.title}</h1>
              <p className="text-gray-700">{selectedVideo.description}</p>
              <p className="text-sm italic mt-1 text-gray-500">{selectedVideo.suggestion}</p>
            </div>
            <div className="flex gap-2 mt-4 sm:mt-0">
              <button
                onClick={() => console.log('Test clicked')}
                className="bg-gray-200 hover:bg-gray-700 hover:text-white transition rounded-2xl px-4 py-2"
              >
                Test Review
              </button>
              <button
                onClick={() => console.log('Feedback clicked')}
                className="bg-gray-200 hover:bg-gray-700 hover:text-white transition rounded-2xl px-4 py-2"
              >
                Feedback
              </button>
            </div>
          </div>
        </div>
      )}

      {/* Categories + Cards */}
      {categories.map((category, idx) => (
        <Disclosure key={idx}>
          {({ open }) => (
            <div className="mb-4">
              <Disclosure.Button className="flex items-center justify-between w-full py-3 text-xl font-semibold focus:outline-none">
                <span>{category.name}</span>
                <ChevronDown className={`h-5 w-5 transition-transform duration-300 ${open ? 'rotate-180' : ''}`} />
              </Disclosure.Button>
              <Disclosure.Panel>
                {category.videos && category.videos.length > 0 ? (
                  <div className="grid grid-cols-1 sm:grid-cols-2 md:grid-cols-4 gap-4 mt-2">
                    {category.videos.map((video, i) => (
                      <div
                        key={i}
                        onClick={() => handleCardClick(video)}
                        className="bg-white rounded-xl shadow p-3 cursor-pointer hover:shadow-lg transition"
                      >
                        <div className="h-40 bg-gray-300 rounded-md mb-2 flex items-center justify-center">
                          <span className="text-gray-600">Video Thumbnail</span>
                        </div>
                        <h3 className="font-medium">{video.title}</h3>
                        <p className="text-sm text-gray-500">{video.learners} learners</p>
                        <div className="text-yellow-500 mt-1">
                          {'★'.repeat(video.rating)}{'☆'.repeat(5 - video.rating)}
                        </div>
                      </div>
                    ))}
                  </div>
                ) : (
                  <div className="text-gray-500 italic mt-2">No videos in this category.</div>
                )}
              </Disclosure.Panel>
            </div>
          )}
        </Disclosure>
      ))}
    </div>
  );
}
