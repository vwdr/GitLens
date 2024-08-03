from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from .routers import helloworld, analyze, testing

app = FastAPI()

# List of allowed origins (i.e., the frontend URLs that you want to allow to access your backend)
origins = [
    "http://localhost:5173",  # Adjust the port if your React app runs on a different one
    "http://localhost:3000",  # Common React development server port
    "http://localhost",
]

# Add CORSMiddleware to the application instance
app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,  # Allows all origins
    allow_credentials=True,
    allow_methods=["*"],  # Allows all methods
    allow_headers=["*"],  # Allows all headers
)

app.include_router(helloworld.router)
app.include_router(analyze.router)
app.include_router(testing.router)
