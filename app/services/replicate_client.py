from typing import Any

import replicate

from app.core.config import settings

_client = replicate.Client(api_token=settings.replicate_api_token)


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
    canny_image_url: str,
    ip_adapter_image_url: str | None,
    lora_weights_url: str | None,
    prompt: str,
    negative_prompt: str,
) -> Any:
    """Single chained call: structural Grid/Vector style + brand LoRA (or generic
    Brand Asset LoRA) + ControlNet Canny (grid fidelity) + IP-Adapter (brand
    colors/mood) feeding one Flux/SDXL prediction."""
    model_input = {
        "prompt": prompt,
        "negative_prompt": negative_prompt,
        "control_image": canny_image_url,
        "controlnet_conditioning_scale": 0.85,
        "guidance_scale": 4.0,
        "num_inference_steps": 28,
    }
    if lora_weights_url:
        model_input["lora_weights"] = lora_weights_url
        model_input["lora_scale"] = 0.8
    if ip_adapter_image_url:
        model_input["ip_adapter_image"] = ip_adapter_image_url
        model_input["ip_adapter_scale"] = 0.6

    prediction = _client.predictions.create(
        version=settings.flux_controlnet_model,
        input=model_input,
    )
    return prediction


def get_prediction(prediction_id: str) -> Any:
    return _client.predictions.get(prediction_id)
