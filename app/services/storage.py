import os
import shutil
import zipfile

from app.core.config import settings


def asset_dir(brand_id: str) -> str:
    path = os.path.join(settings.storage_dir, "assets", brand_id)
    os.makedirs(path, exist_ok=True)
    return path


def save_upload(brand_id: str, filename: str, content: bytes) -> str:
    path = os.path.join(asset_dir(brand_id), filename)
    with open(path, "wb") as f:
        f.write(content)
    return path


def zip_brand_assets(brand_id: str) -> str:
    src_dir = asset_dir(brand_id)
    zip_path = os.path.join(settings.storage_dir, "assets", f"{brand_id}.zip")
    if os.path.exists(zip_path):
        os.remove(zip_path)
    with zipfile.ZipFile(zip_path, "w") as zf:
        for fname in os.listdir(src_dir):
            zf.write(os.path.join(src_dir, fname), arcname=fname)
    return zip_path


def output_path(job_id: str, ext: str = "png") -> str:
    path = os.path.join(settings.storage_dir, "outputs")
    os.makedirs(path, exist_ok=True)
    return os.path.join(path, f"{job_id}.{ext}")


def grid_paths(job_id: str) -> tuple[str, str]:
    base = os.path.join(settings.storage_dir, "grids")
    os.makedirs(base, exist_ok=True)
    return os.path.join(base, f"{job_id}_grid.png"), os.path.join(base, f"{job_id}_canny.png")
