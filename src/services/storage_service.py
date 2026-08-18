import os
import uuid
from fastapi import UploadFile
from core.config import settings
from core.logger import logger

class StorageService:
    def __init__(self):
        self.upload_dir = settings.UPLOAD_DIR
        os.makedirs(self.upload_dir, exist_ok=True)

    async def save_file(self, file: UploadFile, max_size: int = None) -> tuple[str, int]:
        """
        Saves the uploaded file to the local disk.
        Returns the file path and file size in bytes.
        """
        file_ext = os.path.splitext(file.filename)[1] if file.filename else ""
        unique_filename = f"{uuid.uuid4()}{file_ext}"
        file_path = os.path.join(self.upload_dir, unique_filename)

        file_size = 0
        try:
            with open(file_path, 'wb') as out_file:
                while content := await file.read(1024 * 1024):  # 1MB chunks
                    file_size += len(content)
                    if max_size and file_size > max_size:
                        raise ValueError(f"File size exceeds the maximum limit of {max_size} bytes.")
                    out_file.write(content)
            logger.info(f"File saved successfully: {file_path} ({file_size} bytes)")
        except Exception as e:
            logger.error(f"Failed to save file: {e}")
            if os.path.exists(file_path):
                os.remove(file_path)
            raise e
        
        return file_path, file_size

    def delete_file(self, file_path: str) -> bool:
        """
        Deletes the file from local disk.
        """
        if os.path.exists(file_path):
            try:
                os.remove(file_path)
                logger.info(f"File deleted successfully: {file_path}")
                return True
            except OSError as e:
                logger.error(f"Failed to delete file {file_path}: {e}")
                return False
        return False
