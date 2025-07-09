# MicroLearning Backend

This is the backend for the MicroLearning platform, a MERN stack application.

## Getting Started

### Prerequisites

*   Node.js
*   npm
*   MongoDB

### Installation

1.  Clone the repository:
    ```bash
    git clone https://github.com/your-username/microlearning.git
    ```
2.  Navigate to the backend directory:
    ```bash
    cd microlearning/backend
    ```
3.  Install the dependencies:
    ```bash
    npm install
    ```
4.  Create a `.env` file in the root of the backend directory and add the following environment variables:
    ```
    PORT=5000
    MONGO_URI=your_mongodb_connection_string
    JWT_SECRET=your_jwt_secret
    ```

### Usage

To start the server, run the following command:

```bash
npm start
```

The server will start on the port specified in your `.env` file (e.g., http://localhost:5000).

## API Endpoints

The following are the available API endpoints:

*   `POST /api/auth/register`: Register a new user.
*   `POST /api/auth/login`: Log in a user.
*   `GET /api/user/:id`: Get user details.

## Technologies Used

*   Node.js
*   Express
*   MongoDB
*   Mongoose
*   JSON Web Tokens (JWT)
*   bcrypt
*   express-validator
*   Helmet
*   CORS
*   dotenv
*   morgan
*   nodemon
