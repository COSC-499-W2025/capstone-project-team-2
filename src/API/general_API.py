from fastapi import FastAPI
from .analysis_API import analysisRouter
from .consent_API import consentRouter
from .skills_API import skillsRouter
from .project_io_API import projectsRouter
from .Resume_Generator_API import resumeRouter

app = FastAPI()

app.include_router(analysisRouter)
app.include_router(consentRouter)
app.include_router(projectsRouter)
app.include_router(skillsRouter)
app.include_router(resumeRouter)