from typing import Any

import replicate

from app.core.config import settings

_client = replicate.Client(api_token=settings.replicate_api_token)


def _webhook_kwargs() -> dict:
    """Attaches a Replicate webhook callback when APP_BASE_URL is configured,
    so completion is pushed to us instead of relying solely on polling."""
    if not settings.app_base_url:
        return {}
    return {
        "webhook": f"{settings.app_base_url.rstrip('/')}/webhooks/replicate",
        "webhook_events_filter": ["completed"],
    }


def start_lora_training(zip_url: str, trigger_word: str) -> Any:
    """Kicks off a fast LoRA training run for a brand's 15-20 reference images.
    Mirrors the 'Dynamic LoRA Approach': train a lightweight, brand-specific
    LoRA on the fly instead of relying on a static third-party LoRA."""
    training = _client.trainings.create(
        version=settings.lora_trainer_model,
        input={
            "input_images": zip_url,
            "trigger_word": trigger_word,
            "steps": 1000,
        },
        destination=f"momentocards/{trigger_word}-lora",
    )
    return training


def get_training(training_id: str) -> Any:
    return _client.trainings.get(training_id)


def generate_calendar_page(
    canny_image_url: Any | None,
    ip_adapter_image_url: str | None,
    lora_weights_url: str | None,
    prompt: str,
    negative_prompt: str,
) -> Any:
    """Single chained call: structural layout/style tags + brand LoRA (or generic
    Brand Asset LoRA) + ControlNet Canny (only for grid layouts that need exact
    line fidelity) + IP-Adapter (brand colors/mood) feeding one Flux/SDXL
    prediction. `canny_image_url` is None for layouts with no code-generated
    grid (flyers, posters, brochures, ...)."""
    model_input = {
        "prompt": prompt,
        "negative_prompt": negative_prompt,
        "guidance_scale": 4.0,
        "num_inference_steps": 28,
    }
    if canny_image_url is not None:
        model_input["control_image"] = canny_image_url
        model_input["controlnet_conditioning_scale"] = 0.85
    if lora_weights_url:
        model_input["lora_weights"] = lora_weights_url
        model_input["lora_scale"] = 0.8
    if ip_adapter_image_url:
        model_input["ip_adapter_image"] = ip_adapter_image_url
        model_input["ip_adapter_scale"] = 0.6

    prediction = _client.predictions.create(
        version=settings.flux_controlnet_model,
        input=model_input,
        **_webhook_kwargs(),
    )
    return prediction


def start_video_from_keyframe(keyframe_image_url: str, prompt: str | None = None) -> Any:
    """Generates a short video using a previously-generated image as the
    keyframe (img2vid)."""
    model_input: dict = {"input_image": keyframe_image_url}
    if prompt:
        model_input["prompt"] = prompt

    prediction = _client.predictions.create(
        version=settings.video_model,
        input=model_input,
        **_webhook_kwargs(),
    )
    return prediction


def get_prediction(prediction_id: str) -> Any:
    return _client.predictions.get(prediction_id)
