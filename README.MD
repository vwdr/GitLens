# GitLens Documentation

## Overview

**GitLens** is a tool designed to evaluate the technical strengths of candidates based on their GitHub repositories. By analyzing the code and projects present in a given GitHub link, GitLens provides a detailed assessment of the candidate’s expertise in various technical fields as specified by recruiters. This tool streamlines the evaluation process, saving recruiters the time and effort required to manually inspect GitHub repositories and codebases.

## Features

- **Automated Assessment**: GitLens uses GitHub APIs to fetch data from repositories and employs machine learning models to analyze and evaluate the technical skills demonstrated in the code.
- **Customizable Evaluation Criteria**: Recruiters can specify the technical fields and areas of interest they want to assess, and GitLens tailors the evaluation accordingly.
- **Speed and Efficiency**: Provides quick and accurate assessments, significantly reducing the time required to evaluate candidates compared to traditional methods.
- **Comprehensive Reporting**: Generates detailed reports on candidates' strengths in specified technical areas, offering insights that go beyond surface-level code quality.

## Use Case Example

Consider a sophomore in college who has participated in hackathons and developed applications from front to end but lacks formal training in algorithmic coding (such as the content often found in LeetCode or CodeSignal interviews). This candidate might be at a disadvantage compared to peers with more formal education in these areas. Traditional online assessments might not fully capture the candidate’s practical skills and project experience. GitLens provides a more accurate and comprehensive evaluation, offering recruiters a clearer picture of the candidate’s abilities and potential.

## How It Works

1. **Data Retrieval**: GitLens uses the GitHub API to fetch repository data.
2. **Code Extraction and Analysis**: Relevant code is extracted and analyzed using TogetherAI’s tools and models.
3. **Evaluation Algorithm**: An algorithm processes the data and computes the candidate’s strengths in the specified technical fields.
4. **Report Generation**: GitLens generates a report detailing the candidate’s skills and strengths based on the analysis.

## Technology Stack

### Frontend

- **React**
- **TypeScript**
- **Vite**

### Backend

- **FastAPI**
- **Python**

### Additional Tools

- **Docker**
- **GraphQL**
- **TogetherAI**

## Frontend Setup

### Overview

The frontend of GitLens is built using React, TypeScript, and Vite. This setup ensures a fast, scalable, and maintainable codebase with hot module replacement (HMR) for efficient development.

### Prerequisites

- Node.js (LTS version recommended)
- npm or Yarn

### Getting Started

1. **Clone the Repository**:

    ```bash
    git clone <repository-url>
    cd frontend
    ```

2. **Install Dependencies**:

    ```bash
    npm install
    ```

3. **Run the Development Server**:

    ```bash
    npm run dev
    ```

### ESLint Configuration

For production applications, it’s recommended to expand the ESLint configuration to enable type-aware lint rules.

1. **Configure parserOptions**:

    ```javascript
    export default {
      parserOptions: {
        ecmaVersion: 'latest',
        sourceType: 'module',
        project: ['./tsconfig.json', './tsconfig.node.json'],
        tsconfigRootDir: __dirname,
      },
    }
    ```

2. **Update ESLint Plugins**:

    - Replace `plugin:@typescript-eslint/recommended` with `plugin:@typescript-eslint/recommended-type-checked` or `plugin:@typescript-eslint/strict-type-checked`.
    - Optionally add `plugin:@typescript-eslint/stylistic-type-checked`.
    - Install `eslint-plugin-react` and add `plugin:react/recommended` & `plugin:react/jsx-runtime` to the extends list.

## Backend Setup

### Overview

The backend of GitLens is implemented using FastAPI, a modern, fast (high-performance), web framework for building APIs with Python. The backend service is containerized using Docker for easy deployment and scalability.

### Prerequisites

- Docker
- Docker Compose

### Getting Started

1. **Clone the Repository**:

    ```bash
    git clone <repository-url>
    cd backend
    ```

2. **Build the Docker Container**:

    ```bash
    docker-compose build
    ```

3. **Run the Service**:

    ```bash
    docker-compose up
    ```

    The FastAPI server will be accessible at [http://localhost:8000](http://localhost:8000).

### Endpoints

- **Hello World**: A simple endpoint to test the service.

    - **GET /hello/{name}**: Returns a greeting message to the specified name.

    **Example Request**:

    ```http
    GET /hello/John
    ```

    **Example Response**:

    ```json
    {
        "message": "Hello World, John"
    }
    ```

### Stopping the Service

To stop the running Docker container, use the following command:

```bash
docker-compose down
```

### Dependencies

- fastapi==0.75.0
- uvicorn==0.17.6
- together
- python-dotenv
- openai
- aiohttp
- firebase_admin

## Conclusion

GitLens is a powerful tool for recruiters looking to evaluate the technical skills of candidates efficiently and accurately. By leveraging advanced technologies and a well-structured technology stack, GitLens provides comprehensive insights into candidates' abilities, helping recruiters make informed decisions quickly. Whether you are a recruiter looking to streamline your hiring process or a developer aiming to showcase your skills, GitLens offers a robust solution for technical evaluations.