from fastapi import APIRouter, Depends
from pydantic import BaseModel

from iresume.api.deps import get_profile_repo
from iresume.storage.profile_repository import ProfileRepository

router = APIRouter()


class ProfileUpdateRequest(BaseModel):
    content: str


@router.get("/")
async def get_profile(repo: ProfileRepository = Depends(get_profile_repo)):
    return {
        "education": repo.read_raw("education.md"),
        "experience": repo.read_raw("experience.md"),
        "skills": repo.read_raw("skills.md"),
    }


@router.put("/education")
async def update_education(
    request: ProfileUpdateRequest,
    repo: ProfileRepository = Depends(get_profile_repo),
):
    repo.write_raw("education.md", request.content)
    return {"status": "ok"}


@router.put("/experience")
async def update_experience(
    request: ProfileUpdateRequest,
    repo: ProfileRepository = Depends(get_profile_repo),
):
    repo.write_raw("experience.md", request.content)
    return {"status": "ok"}


@router.put("/skills")
async def update_skills(
    request: ProfileUpdateRequest,
    repo: ProfileRepository = Depends(get_profile_repo),
):
    repo.write_raw("skills.md", request.content)
    return {"status": "ok"}
