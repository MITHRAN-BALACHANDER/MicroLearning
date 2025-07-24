import { createSlice, nanoid } from '@reduxjs/toolkit';

// Function to generate category based on tags/description
const generateCategory = (tags, description) => {
  const text = `${tags} ${description}`.toLowerCase();
  
  if (text.includes('money') || text.includes('budget') || text.includes('invest') || text.includes('finance') || text.includes('loan')) {
    return 'Finance';
  } else if (text.includes('business') || text.includes('startup') || text.includes('entrepreneur') || text.includes('company')) {
    return 'Business';
  } else if (text.includes('bank') || text.includes('account') || text.includes('credit') || text.includes('debit')) {
    return 'Banking';
  } else if (text.includes('market') || text.includes('brand') || text.includes('advertis') || text.includes('promotion')) {
    return 'Marketing';
  } else if (text.includes('estimate') || text.includes('cost') || text.includes('price') || text.includes('valuation')) {
    return 'Estimation';
  } else {
    return 'Business'; // Default category
  }
};

const initialState = {
  categories: [
    { 
      name: 'Finance', 
      videos: [
        {
          id: 'dummy-finance-1',
          title: 'Personal Budget Planning',
          learners: 15,
          rating: 4,
          src: '/videos/sample.mp4',
          description: 'Learn how to create and stick to a personal budget.',
          suggestion: 'Start with the 50-30-20 rule',
          category: 'Finance',
          tags: 'budget, planning, money',
          status: 'accepted',
          uploadedAt: new Date().toLocaleString()
        },
        {
          id: 'dummy-finance-2',
          title: 'Investment Fundamentals',
          learners: 23,
          rating: 5,
          src: '/videos/sample.mp4',
          description: 'Basic principles of investing for beginners.',
          suggestion: 'Diversify your portfolio',
          category: 'Finance',
          tags: 'investment, stocks, portfolio',
          status: 'accepted',
          uploadedAt: new Date().toLocaleString()
        }
      ]
    },
    { 
      name: 'Business', 
      videos: [
        {
          id: 'dummy-business-1',
          title: 'Starting Your First Business',
          learners: 18,
          rating: 4,
          src: '/videos/sample.mp4',
          description: 'Essential steps to launch a successful business.',
          suggestion: 'Validate your idea first',
          category: 'Business',
          tags: 'startup, entrepreneur, business plan',
          status: 'accepted',
          uploadedAt: new Date().toLocaleString()
        },
        {
          id: 'dummy-business-2',
          title: 'Business Model Canvas',
          learners: 12,
          rating: 5,
          src: '/videos/sample.mp4',
          description: 'How to create a comprehensive business model.',
          suggestion: 'Focus on your value proposition',
          category: 'Business',
          tags: 'business model, strategy, planning',
          status: 'accepted',
          uploadedAt: new Date().toLocaleString()
        }
      ]
    },
    { 
      name: 'Banking', 
      videos: [
        {
          id: 'dummy-banking-1',
          title: 'Understanding Credit Scores',
          learners: 8,
          rating: 4,
          src: '/videos/sample.mp4',
          description: 'Learn how credit scores work and how to improve them.',
          suggestion: 'Pay bills on time consistently',
          category: 'Banking',
          tags: 'credit, score, banking',
          status: 'accepted',
          uploadedAt: new Date().toLocaleString()
        }
      ]
    },
    { 
      name: 'Marketing', 
      videos: [
        {
          id: 'dummy-marketing-1',
          title: 'Digital Marketing Basics',
          learners: 25,
          rating: 4,
          src: '/videos/sample.mp4',
          description: 'Introduction to digital marketing strategies.',
          suggestion: 'Start with social media marketing',
          category: 'Marketing',
          tags: 'digital marketing, social media, strategy',
          status: 'accepted',
          uploadedAt: new Date().toLocaleString()
        }
      ]
    },
    { name: 'Estimation', videos: [] }
  ],
  reviewVideos: []
};

const videosSlice = createSlice({
  name: 'videos',
  initialState,
  reducers: {
    addVideoToReview: {
      reducer(state, action) {
        state.reviewVideos.push(action.payload);
      },
      prepare({ title, category }) {
        return {
          payload: {
            id: nanoid(),
            title,
            category,
            description: 'Auto-generated description based on video content analysis.',
            status: 'pending',
            uploadedAt: new Date().toLocaleString()
          }
        };
      }
    },

    // New action for direct video creation with tags and description
    createVideoDirectly: {
      reducer(state, action) {
        const video = action.payload;
        const categoryName = video.category;
        
        // Find the category and add the video
        const category = state.categories.find(
          cat => cat.name.toLowerCase() === categoryName.toLowerCase()
        );
        
        if (category) {
          category.videos.push(video);
        }
      },
      prepare({ title, tags, description, videoFile }) {
        const generatedCategory = generateCategory(tags, description);
        
        return {
          payload: {
            id: nanoid(),
            title,
            tags,
            description,
            category: generatedCategory,
            learners: Math.floor(Math.random() * 20) + 1,
            rating: Math.floor(Math.random() * 5) + 1,
            src: videoFile ? URL.createObjectURL(videoFile) : '/videos/sample.mp4',
            suggestion: 'Auto-generated suggestion based on content',
            status: 'accepted',
            uploadedAt: new Date().toLocaleString()
          }
        };
      }
    },

    acceptVideo(state, action) {
      const idx = state.reviewVideos.findIndex(v => v.id === action.payload);
      if (idx === -1) return;

      const video = { ...state.reviewVideos[idx], status: 'accepted' };
      state.reviewVideos[idx] = video;

      const cat = state.categories.find(
        c => c.name.toLowerCase() === video.category.toLowerCase()
      );
      if (cat) {
        cat.videos.push({ 
          ...video, 
          learners: Math.floor(Math.random() * 20) + 1, 
          rating: Math.floor(Math.random() * 5) + 1, 
          src: '/videos/sample.mp4' 
        });
      }
    },

    rejectVideo(state, action) {
      const vid = state.reviewVideos.find(v => v.id === action.payload);
      if (vid) vid.status = 'rejected';
    }
  }
});

export const { addVideoToReview, createVideoDirectly, acceptVideo, rejectVideo } = videosSlice.actions;
export default videosSlice.reducer;
