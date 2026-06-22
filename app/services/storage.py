import os
import zipfile

import httpx

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


def persist_provider_output(item_id: str, provider_url: str, suffix: str = "") -> str:
    """Downloads a (temporary) Replicate output URL into app-owned storage and
    returns a stable, app-served URL (/storage/outputs/...). Never returns the
    raw provider URL to callers -- provider outputs are not the source of
    truth for long-term storage."""
    ext = provider_url.split("?")[0].rsplit(".", 1)[-1][:5] or "bin"
    filename = f"{item_id}{suffix}.{ext}"
    dest_path = output_path(item_id + suffix, ext)
    with httpx.stream("GET", provider_url, timeout=120) as response:
        response.raise_for_status()
        with open(dest_path, "wb") as f:
            for chunk in response.iter_bytes():
                f.write(chunk)
    return f"/storage/outputs/{filename}"
