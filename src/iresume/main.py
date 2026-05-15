import uvicorn
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from iresume.api.middleware import logging_middleware
from iresume.api.routes import profile, resume
from iresume.config import settings
from iresume.utils.logger import setup_logging

setup_logging()

app = FastAPI(title="IResume", version="0.1.0")

app.middleware("http")(logging_middleware)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(profile.router, prefix="/api/profile", tags=["profile"])
app.include_router(resume.router, prefix="/api/resume", tags=["resume"])


def main():
    uvicorn.run("iresume.main:app", host=settings.host, port=settings.port, reload=True)


if __name__ == "__main__":
    main()
