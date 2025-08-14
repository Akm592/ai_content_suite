# AI Content Transformation Suite - Frontend

This directory contains the Next.js frontend application for the AI Content Transformation Suite. It provides the user interface for interacting with the backend services, allowing users to convert PDFs to audiobooks and create AI-generated storybooks.

## Features

-   **Intuitive User Interface**: A clean and responsive design for easy navigation and interaction.
-   **PDF to Audiobook Conversion**: Upload PDF files and select voice profiles to generate audiobooks.
-   **AI Storybook Creation & Editing**: Input text or upload PDFs to generate storybooks, with capabilities to customize characters, artistic styles, and edit individual scenes.
-   **Dynamic Theme Switching**: Supports light, dark, and system default themes for a personalized viewing experience.

## Technologies Used

-   **Next.js**: React framework for building server-side rendered and static web applications.
-   **React**: JavaScript library for building user interfaces.
-   **TypeScript**: Strongly typed superset of JavaScript that compiles to plain JavaScript.
-   **Tailwind CSS**: A utility-first CSS framework for styling.
-   **next-themes**: A lightweight library for managing themes (light, dark, system) in Next.js applications.
-   **Radix UI**: Unstyled, accessible components for building high-quality design systems.

## Setup (Frontend Only)

If you wish to run the frontend application independently of the Docker Compose setup, follow these steps:

1.  **Navigate to the frontend directory:**
    ```bash
    cd frontend
    ```

2.  **Install dependencies:**
    ```bash
    npm install
    # or yarn install
    # or pnpm install
    ```

3.  **Configure Environment Variables:**
    Create a `.env.local` file in the `frontend` directory and add the backend API URL:
    ```
    NEXT_PUBLIC_API_URL=http://localhost:8000
    ```
    *Note: If your backend is running on a different host or port, adjust the URL accordingly.*

4.  **Run the development server:**
    ```bash
    npm run dev
    # or yarn dev
    # or pnpm dev
    ```

    Open [http://localhost:3000](http://localhost:3000) in your browser to see the application.

## Available Scripts

In the project directory, you can run:

-   `npm run dev`: Runs the application in development mode.
-   `npm run build`: Builds the application for production to the `.next` folder.
-   `npm run start`: Starts a production Next.js server.
-   `npm run lint`: Runs ESLint to check for code quality issues.

## Project Structure

-   `app/`: Contains the main application routes and pages.
-   `components/`: Reusable React components, including UI components (`ui/`).
-   `lib/`: Utility functions and helper modules.
-   `public/`: Static assets like images and fonts.
-   `styles/`: Global CSS and Tailwind CSS configurations.