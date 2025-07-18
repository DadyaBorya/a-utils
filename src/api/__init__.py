from fastapi import APIRouter

from src.api.hsts_mvs_process import router as hsts_mvs_process_router

main_router = APIRouter()

main_router.include_router(hsts_mvs_process_router, prefix='/process')
