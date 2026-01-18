from fastapi import FastAPI
from .analysis_API import analysisRouter
from .project_io_API import projectsRouter

app = FastAPI()

app.include_router(analysisRouter)
app.include_router(projectsRouter)