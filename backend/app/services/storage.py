from pathlib import Path
from uuid import uuid4
from fastapi import UploadFile, HTTPException

UPLOAD_DIR = Path("storage/uploads")
MAX_FILE_SIZE_MB = 500

def validate_file_size(file: UploadFile):
    filename = file.filename or "<unnamed>"
    file_size_mb = len(file.file.read()) / (1024 * 1024)
    file.file.seek(0)  
    if file_size_mb > MAX_FILE_SIZE_MB:
        raise HTTPException(status_code=400, detail=f"File size exceeds {MAX_FILE_SIZE_MB} MB limit.")
    
    if not filename.lower().endswith('.csv'):
        raise HTTPException(status_code=400, detail="Only CSV files are allowed.")
    
    if file.content_type not in {'text/csv', 'application/vnd.ms-excel'}:
        raise HTTPException(status_code=400, detail="Invalid file type. Only CSV files are allowed.")
    
def build_storage_path(filename):
    UPLOAD_DIR.mkdir(parents=True, exist_ok=True)
    
    safe_suffix = Path(filename).suffix.lower()
    unique_name = f"{uuid4().hex}{safe_suffix}"
    return UPLOAD_DIR / unique_name

async def save_upload_file(file):
    validate_file_size(file)
    
    size = 0
    storage_path = build_storage_path(file.filename)
    with storage_path.open("wb") as buffer:
        while True:
            chunk = await file.read(1024 * 1024)  
            size += len(chunk)
            if not chunk:
                break
            buffer.write(chunk)
    
    return {
        'filename': file.filename,
        'storage_name': str(storage_path.name),
        'storage_path': str(storage_path),
        'size': size
    }
    
def get_file_metadata(file_path):
    path = Path(file_path)
    
    if not path.exists():
        raise HTTPException(status_code=404, detail="File not found.")
    
    return {
        'filename': path.name,
        'file_path': str(path),
        'size': path.stat().st_size,
        'created_at': path.stat().st_ctime,
    }