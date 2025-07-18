from fastapi import FastAPI

from src.api import main_router

app = FastAPI(redirect_slashes=False)
app.include_router(main_router)
