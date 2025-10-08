# MicroLearning Admin Panel

A comprehensive admin panel for managing the MicroLearning platform with React, TypeScript, and Node.js.

## Features

### 1. Dashboard
- Overview statistics (total users, videos, categories, ratings)
- Real-time metrics and growth indicators
- Quick stats and engagement overview

### 2. User Management
- View all registered users
- Search and filter users
- Edit user information
- Delete users
- Pagination support

### 3. Category Management
- View all categories with video counts
- Create new categories
- Edit existing categories
- Delete categories (with validation)
- Search categories

### 4. Video Management
- View all videos with detailed stats
- See ratings, views, and category information
- Create new videos
- Edit video details
- Delete videos
- Search and filter videos

### 5. Analytics
- Top-rated videos
- Video distribution by category
- Rating distribution analysis
- User registration trends
- Engagement metrics

### 6. Profile Management
- View admin profile
- Update personal information
- Profile avatar with initials

## Tech Stack

### Frontend
- **React** with TypeScript
- **Vite** for build tooling
- **shadcn/ui** for UI components
- **Tailwind CSS** for styling
- **React Router** for navigation
- **Axios** for API calls
- **Lucide React** for icons

### Backend
- **Node.js** with Express
- **MongoDB** with Mongoose
- **JWT** for authentication
- **Redis** for caching
- **Bcrypt** for password hashing
- **Multer** for file uploads

## Setup Instructions

### Prerequisites
- Node.js (v16 or higher)
- MongoDB
- Redis (optional, for caching)

### Backend Setup

1. Navigate to the backend directory:
```bash
cd backend
```

2. Install dependencies:
```bash
npm install
```

3. Create a `.env` file in the backend directory:
```env
PORT=5000
MONGO_URI=mongodb://localhost:27017/microlearning
JWT_SECRET=your_jwt_secret_key_here
NODE_ENV=development
```

4. Start the backend server:
```bash
npm run dev
```

### Frontend Setup

1. Navigate to the frontend directory:
```bash
cd frontend
```

2. Install dependencies:
```bash
npm install
```

3. The `.env` file is already created with:
```env
VITE_API_URL=http://localhost:5000/api
```

4. Start the development server:
```bash
npm run dev
```

5. Open your browser and navigate to `http://localhost:5173`

## API Endpoints

### Admin Routes
- `GET /api/admin/users` - Get all users with pagination
- `PUT /api/admin/users/:id` - Update user
- `DELETE /api/admin/users/:id` - Delete user
- `GET /api/admin/analytics/dashboard` - Get dashboard analytics
- `GET /api/admin/analytics/videos` - Get video analytics
- `GET /api/admin/analytics/engagement` - Get user engagement data
- `GET /api/admin/categories/stats` - Get categories with stats
- `DELETE /api/admin/categories/:id` - Delete category
- `GET /api/admin/videos/stats` - Get videos with stats
- `DELETE /api/admin/videos/:id` - Delete video
- `GET /api/admin/feedback` - Get all feedback

### Authentication
All admin routes require authentication. Include the JWT token in the Authorization header:
```
Authorization: Bearer <your_token>
```

## Project Structure

```
MicroLearning/
├── backend/
│   ├── controllers/
│   │   ├── adminController.js (NEW)
│   │   ├── authController.js
│   │   ├── categoryController.js
│   │   ├── videoController.js
│   │   └── ...
│   ├── routes/
│   │   ├── adminRoutes.js (NEW)
│   │   └── ...
│   ├── models/
│   │   ├── Admin.js
│   │   ├── User.js
│   │   ├── Category.js
│   │   ├── Video.js
│   │   └── ...
│   └── server.js (UPDATED)
│
├── frontend/
│   ├── src/
│   │   ├── components/
│   │   │   ├── ui/ (shadcn components)
│   │   │   ├── app-sidebar.tsx (UPDATED)
│   │   │   └── ...
│   │   ├── pages/
│   │   │   ├── Dashboard.tsx (NEW)
│   │   │   ├── Users.tsx (NEW)
│   │   │   ├── Categories.tsx (NEW)
│   │   │   ├── Videos.tsx (NEW)
│   │   │   ├── Analytics.tsx (NEW)
│   │   │   └── Profile.tsx (NEW)
│   │   ├── lib/
│   │   │   ├── api.ts (NEW)
│   │   │   └── adminApi.ts (NEW)
│   │   ├── hooks/
│   │   │   └── use-toast.ts (NEW)
│   │   ├── constants/
│   │   │   └── navigation.ts (UPDATED)
│   │   ├── App.tsx (UPDATED)
│   │   └── ...
│   └── .env (NEW)
│
└── README.md (NEW)
```

## Navigation Structure

The sidebar now contains only the essential admin features:
- Dashboard
- Analytics
- Users
- Categories
- Videos
- Profile

All unnecessary navigation items have been removed for a cleaner, more focused admin experience.

## Components Used (shadcn/ui)

- Card, CardContent, CardDescription, CardHeader, CardTitle
- Button
- Input
- Label
- Badge
- Table (with TableBody, TableCell, TableHead, TableHeader, TableRow)
- DropdownMenu
- Avatar, AvatarFallback
- Sidebar components
- Separator
- Toaster (for notifications)

## Development Notes

- All API calls include error handling with toast notifications
- Loading states are implemented for better UX
- Pagination is implemented for large datasets
- Search functionality is available for users and videos
- Form validation is included in profile updates
- Authentication state is managed via localStorage

## Future Enhancements

- Add video upload functionality
- Implement category creation form
- Add user creation/invitation feature
- Export analytics as PDF/CSV
- Advanced filtering options
- Real-time notifications
- Role-based access control
- Activity logs

## License

MIT License
