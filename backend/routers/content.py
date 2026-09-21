"""routers/content.py — CMS publik (Epic E9). GET /api/content (storefront konsumsi)."""
from fastapi import APIRouter

from db import get_db
from services import content as content_svc

router = APIRouter(tags=["content"])


@router.get("/content")
async def get_content():
    return await content_svc.public_content(get_db())
