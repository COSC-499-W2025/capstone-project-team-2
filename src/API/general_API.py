from fastapi import FastAPI
from .analysis_API import analysisRouter
from .consent_API import consentRouter

from .project_io_API import projectsRouter

app = FastAPI()

app.include_router(analysisRouter)
app.include_router(consentRouter)
app.include_router(projectsRouter)