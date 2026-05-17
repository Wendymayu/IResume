from fastapi import APIRouter, Depends
from pydantic import BaseModel

from iresume.api.deps import get_profile_repo
from iresume.models.profile import PersonalInfo
from iresume.storage.profile_repository import ProfileRepository

router = APIRouter()


class ProfileUpdateRequest(BaseModel):
    content: str


class PersonalInfoRequest(BaseModel):
    name: str = ""
    age: int | None = None
    email: str = ""
    phone: str = ""
    desired_position: str = ""


@router.get("/")
async def get_profile(repo: ProfileRepository = Depends(get_profile_repo)):
    return {
        "personal_info": repo.read_personal_info().model_dump(),
        "education": repo.read_raw("education.md"),
        "experience": repo.read_raw("experience.md"),
        "skills": repo.read_raw("skills.md"),
    }


@router.get("/personal-info")
async def get_personal_info(repo: ProfileRepository = Depends(get_profile_repo)):
    return repo.read_personal_info().model_dump()


@router.put("/personal-info")
async def update_personal_info(
    request: PersonalInfoRequest,
    repo: ProfileRepository = Depends(get_profile_repo),
):
    repo.write_personal_info(PersonalInfo(**request.model_dump()))
    return {"status": "ok"}


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
