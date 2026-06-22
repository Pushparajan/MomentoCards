from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    replicate_api_token: str = ""
    database_url: str = "sqlite:///./momentocards.db"
    storage_dir: str = "./storage"

    # Replicate model refs (override via env as Replicate updates versions)
    lora_trainer_model: str = "replicate/fast-flux-trainer"
    flux_controlnet_model: str = "xlabs-ai/flux-dev-controlnet"
    ip_adapter_model: str = "fofr/sdxl-ip-adapter"
    video_model: str = "stability-ai/stable-video-diffusion"

    # Public base URL this API is reachable at, used to build Replicate webhook
    # callback URLs (https://<app_base_url>/webhooks/replicate). Polling against
    # GET /deliverables/{id} still works as a fallback when this is unset.
    app_base_url: str = ""

    class Config:
        env_file = ".env"


settings = Settings()
