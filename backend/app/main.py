"""
Main FastAPI application entry point.
"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.api import auth, chat, preprocessing, tools, citations
from app.middleware.logging_middleware import LoggingMiddleware

import os

# App creation
app = FastAPI(
    title="Court Case Q&A API",
    description="Backend API for court case question answering system",
    version="0.1.0",
)

# CORS middleware
# In production, set ALLOWED_ORIGINS to your frontend URL (e.g. "https://courtqa.vercel.app")
# Multiple origins can be comma-separated
origins = ["*"]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,  # allow cookies and Authorization headers
    allow_methods=["*"],
    allow_headers=["*"],  # allow all headers

)

# HTTP logging middleware (captures all requests/responses)
app.add_middleware(LoggingMiddleware)

# Route registration
app.include_router(auth.router)
app.include_router(chat.router)
app.include_router(preprocessing.router)
app.include_router(tools.router)
app.include_router(citations.router)


# Root endpoint
@app.get("/")
async def root():
    """Health check endpoinnt."""
    return {
        "message": "Court Case Q&A API",
        "status": "running",
    }
