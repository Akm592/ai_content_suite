# AI Content Transformation Suite - Backend

This directory contains the Python FastAPI backend application for the AI Content Transformation Suite. It provides the core logic for processing PDF documents, generating audio, creating images, and assembling storybooks using various AI services.

## Features

-   **PDF Parsing**: Extracts text content from PDF documents.
-   **Text-to-Speech (TTS) Conversion**: Converts text into natural-sounding audio using Google Cloud TTS.
-   **Image Generation**: Generates images based on textual descriptions using Generative AI models.
-   **Storybook Assembly**: Combines text and generated images into a cohesive storybook format, often outputting as a PDF.
-   **Session Management**: Manages ongoing storybook creation sessions, allowing for iterative editing and regeneration of content.

## Technologies Used

-   **Python**: The primary programming language.
-   **FastAPI**: A modern, fast (high-performance) web framework for building APIs with Python 3.7+ based on standard Python type hints.
-   **Pydantic**: Used by FastAPI for data validation and settings management.
-   **Redis**: An in-memory data structure store, used for caching and managing session states for storybook creation.
-   **python-multipart**: For handling file uploads.
-   **Google Cloud Client Libraries**: For interacting with Google's AI services (e.g., Text-to-Speech, Generative AI).
-   **PyPDF2**: For PDF manipulation and parsing.

## Setup (Backend Only)

If you wish to run the backend application independently of the Docker Compose setup, follow these steps:

1.  **Navigate to the backend directory:**
    ```bash
    cd backend
    ```

2.  **Create and activate a virtual environment (recommended):**
    ```bash
    python -m venv venv
    source venv/bin/activate  # On Windows, use `venv\Scripts\activate`
    ```

3.  **Install dependencies:**
    ```bash
    pip install -r requirements.txt
    ```

4.  **Environment Variables:**
    Create a `.env` file in the `backend` directory with your Google API Key and Redis configuration:
    ```
    GOOGLE_API_KEY=your_google_api_key_here
    REDIS_HOST=localhost
    REDIS_PORT=6379
    ```
    *Note: Ensure your Google API Key has access to Text-to-Speech and Generative AI services.*

5.  **Run the application:**
    ```bash
    uvicorn main:app --host 0.0.0.0 --port 8000 --reload
    ```
    The API will be accessible at `http://localhost:8000`.

## API Endpoints

### Audiobook Conversion
-   `POST /audiobook/convert`: Converts a PDF file to an audiobook.

### Storybook Creation
-   `POST /storybook/create-and-finalize`: Creates a storybook directly from text or PDF and provides a download.
-   `POST /storybook/session/start`: Initiates a storybook creation session for iterative editing.
-   `GET /storybook/session/{session_id}/state`: Retrieves the current state of a storybook session.
-   `PUT /storybook/session/{session_id}/scene/{scene_index}`: Updates the text of a specific scene in a session.
-   `POST /storybook/session/{session_id}/scene/{scene_index}/regenerate`: Regenerates the image for a specific scene.
-   `PUT /storybook/session/{session_id}/details`: Updates storybook title and author.
-   `PUT /storybook/session/{session_id}/styles`: Updates storybook font styles.
-   `GET /storybook/session/{session_id}/preview`: Generates a PDF preview of the current storybook session.
-   `GET /storybook/session/{session_id}/download`: Finalizes and provides a download of the storybook PDF.

## Project Structure

-   `main.py`: The main FastAPI application entry point.
-   `redis_client.py`: Handles Redis client connections.
-   `pdf_to_audiobook/`: Contains modules for PDF parsing and TTS generation.
-   `storybook_creator/`: Contains modules for narrative processing, image generation, and PDF assembly.
-   `requirements.txt`: Lists Python dependencies.

