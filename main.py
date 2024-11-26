import os
import uuid
from typing import Annotated, List

from fastapi import (
    FastAPI, 
    File, 
    UploadFile, 
    HTTPException, 
    status, 
    APIRouter, 
    Depends
)
from fastapi.responses import FileResponse, JSONResponse
from pydantic import BaseModel

UPLOAD_DIR = "uploaded_images"
os.makedirs(UPLOAD_DIR, exist_ok=True)

class ImageMetadata(BaseModel):
    filename: str
    original_name: str
    size: int
    content_type: str

image_router = APIRouter(prefix="/images", tags=["images"])

@image_router.post("/upload", response_model=ImageMetadata)
async def upload_image(
    file: UploadFile = File(...)
    ) -> ImageMetadata:
    
    if file.size > 10_000_000:
        raise HTTPException(
            status_code=status.HTTP_413_PAYLOAD_TOO_LARGE, 
            detail="File too large. Max 10MB allowed."
        )
    
    allowed_types = {
        "image/jpeg", 
        "image/png", 
        "image/gif", 
        "image/webp"
    }

    if file.content_type not in allowed_types:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, 
            detail="Invalid file type. Only JPEG, PNG, GIF, and WebP allowed."
        )
    
    try:
        file_ext = file.filename.split(".")[-1]
        unique_filename = f"{uuid.uuid4()}.{file_ext}"
        file_path = os.path.join(UPLOAD_DIR, unique_filename)

        with open(file_path, "wb") as buffer:
            content = await file.read()
            buffer.write(content)
        
        return ImageMetadata(
            filename=unique_filename,
            original_name=file.filename,
            size=len(content),
            content_type=file.content_type
        )
    
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, 
            detail=f"Upload failed: {str(e)}"
        )
    finally:
        await file.close()

@image_router.get("/download/{filename}")
async def download_image(filename: str):
    file_path = os.path.join(UPLOAD_DIR, filename)
    
    if not os.path.exists(file_path):
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, 
            detail="Image not found"
        )
    
    content_type_map = {
        ".jpg": "image/jpeg",
        ".jpeg": "image/jpeg",
        ".png": "image/png",
        ".gif": "image/gif",
        ".webp": "image/webp"
    }
    
    file_ext = os.path.splitext(filename)[1].lower()
    content_type = content_type_map.get(file_ext, "application/octet-stream")
    
    return FileResponse(
        path=file_path, 
        media_type=content_type, 
        filename=filename
    )

app = FastAPI(title="Image Upload/Download API")

app.include_router(image_router)


@app.get("/square")
async def get_square():
    return 2 ** 2 