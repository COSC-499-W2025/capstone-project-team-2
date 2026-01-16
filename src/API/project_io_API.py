from fastapi import APIRouter, UploadFile

projectsRouter = APIRouter(
    prefix="/projects"
)

#Todo
@projectsRouter.post("/upload")
async def upload_project(upload_file: UploadFile):
    pass

#Todo
@projectsRouter.get("/")
def return_all_saved_projects():
    return "all saved projects"

#Todo
@projectsRouter.get("/{id}")
def get_project_by_name(project_name: str):
    return id