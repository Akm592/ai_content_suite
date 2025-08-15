# AI Content Transformation Suite

The AI Content Transformation Suite is a full-stack application designed to transform various forms of content using artificial intelligence. It currently offers two main functionalities: converting PDF documents into audiobooks and creating AI-generated storybooks from text or PDFs.

## Features

-   **PDF to Audiobook Converter**: Upload a PDF, select a voice profile, and convert it into an audiobook.
-   **AI Storybook Creator**: Generate illustrated storybooks from provided text or PDF documents, with options to customize characters, artistic style, and edit scenes.
-   **Theme Support**: Toggle between light, dark, and system default themes for a personalized user experience.

## Technologies Used

### Frontend
-   **Next.js**: React framework for building server-side rendered and static web applications.
-   **React**: JavaScript library for building user interfaces.
-   **Tailwind CSS**: A utility-first CSS framework for rapid UI development.
-   **next-themes**: For managing light/dark/system themes.

### Backend
-   **Python**: Primary programming language.
-   **FastAPI**: Modern, fast (high-performance) web framework for building APIs with Python 3.7+.
-   **Redis**: In-memory data structure store, used for caching and session management.
-   **Google Cloud APIs**: Utilized for Text-to-Speech (TTS) and Generative AI (e.g., image generation).

### Infrastructure
-   **Docker**: For containerization of frontend, backend, and Redis services.
-   **Docker Compose**: For defining and running multi-container Docker applications.

## Setup

To get the AI Content Transformation Suite up and running on your local machine, follow these steps:

1.  **Clone the repository:**
    ```bash
    git clone https://github.com/your-username/ai_content_suite.git
    cd ai_content_suite
    ```

2.  **Environment Variables:**
    Create a `.env` file in the `backend` directory with your Google API Key:
    ```
    GOOGLE_API_KEY=your_google_api_key_here
    ```
    *Note: Ensure your Google API Key has access to Text-to-Speech and Generative AI services.*

3.  **Build and Run with Docker Compose:**
    From the root directory of the project, run:
    ```bash
    docker-compose up --build
    ```
    This command will:
    -   Build the Docker images for the frontend and backend services.
    -   Start the Redis service.
    -   Start the backend API server (on `http://localhost:8000`).
    -   Start the Next.js frontend development server (on `http://localhost:3000`).

4.  **Access the Application:**
    Open your web browser and navigate to `http://localhost:3000`.

## Project Structure

-   `backend/`: Contains the Python FastAPI application, including PDF parsing, TTS, and image generation logic.
-   `frontend/`: Contains the Next.js React application for the user interface.
-   `docker-compose.yml`: Defines the multi-service Docker environment.

## Contributing

Contributions are welcome! Please feel free to submit a pull request or open an issue.

## License


