from fastapi import UploadFile, File, HTTPException, APIRouter

from src.services.hsts_mvs_process import HstsMvsProcess

router = APIRouter(prefix="/hsts-mvs")


@router.post('')
async def process(file: UploadFile = File(...)):
    if not file.filename.endswith(".pdf"):
        raise HTTPException(status_code=400, detail="Не вірний формат файлу.")

    encoded_pdf, encoded_image = await HstsMvsProcess().process(file)

    return {
        "pdf": encoded_pdf,
        "image": encoded_image
    }
