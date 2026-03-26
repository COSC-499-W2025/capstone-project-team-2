from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import os
from .analysis_API import analysisRouter
from .consent_API import consentRouter
from .skills_API import skillsRouter
from .project_io_API import projectsRouter
from .Resume_Generator_API import resumeRouter
from .Portfolio_Generator_API import portfolioRouter
from .representation_API import representationRouter
from .project_insights_API import insights_router

app = FastAPI(
    title="DevDoc API",
    description="API for analysing projects and generating resumes and portfolios.",
    version="1.0.0",
)

# Allow deployment environments to inject custom origins.
cors_origins_env = os.getenv("CORS_ORIGINS", "")
cors_origins = [origin.strip() for origin in cors_origins_env.split(",") if origin.strip()]
if not cors_origins:
    cors_origins = [
        "http://localhost:3000",
        "http://127.0.0.1:3000",
    ]

app.add_middleware(
    CORSMiddleware,
    allow_origins=cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(analysisRouter)
app.include_router(consentRouter)
app.include_router(projectsRouter)
app.include_router(skillsRouter)
app.include_router(portfolioRouter)
app.include_router(representationRouter)
app.include_router(resumeRouter)
app.include_router(insights_router)
