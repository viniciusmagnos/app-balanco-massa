import json
import logging

from openai import OpenAI

from ...config import settings

logger = logging.getLogger(__name__)

SYSTEM_PROMPT = (
    "You are an expert civil engineering CAD analyst. "
    "You analyze DXF/DWG longitudinal road profile drawings. "
    "Respond ONLY with valid JSON, no extra text."
)


def _get_client() -> OpenAI | None:
    if not settings.openai_api_key:
        return None
    return OpenAI(api_key=settings.openai_api_key)


def analyze_layers(layer_stats: dict) -> dict | None:
    """Ask GPT to classify layers as greide/terreno.

    layer_stats: {layer_name: {entity_types: [...], count: N, total_length: F}}
    Returns: {"greide": "layer_name", "terreno": "layer_name"} or None.
    """
    client = _get_client()
    if not client:
        return None

    prompt = (
        "Given these CAD layers from a longitudinal road profile drawing, "
        "identify which layer is the design grade line (greide/projeto) and "
        "which is the terrain/ground profile.\n\n"
        f"Layers:\n{json.dumps(layer_stats, indent=2, ensure_ascii=False)}\n\n"
        "Respond with JSON: {\"greide\": \"layer_name\", \"terreno\": \"layer_name\"}"
    )

    try:
        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user", "content": prompt},
            ],
            timeout=10,
            max_tokens=200,
        )
        text = response.choices[0].message.content.strip()
        return json.loads(text)
    except Exception as e:
        logger.warning(f"LLM layer analysis failed: {e}")
        return None


def analyze_sections(geometry_summary: dict, texts: list[dict]) -> list[dict] | None:
    """Ask GPT to identify sections from geometry and text data.

    Returns list of {x_start, x_end, initial_station} or None.
    """
    client = _get_client()
    if not client:
        return None

    text_sample = texts[:50]  # limit context
    prompt = (
        "Analyze this road profile CAD data and identify distinct sections (trechos).\n\n"
        f"Geometry summary:\n{json.dumps(geometry_summary, indent=2)}\n\n"
        f"Text elements (sample):\n{json.dumps(text_sample, indent=2, ensure_ascii=False)}\n\n"
        "Respond with JSON array: [{\"x_start\": N, \"x_end\": N, \"initial_station\": N}]"
    )

    try:
        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user", "content": prompt},
            ],
            timeout=10,
            max_tokens=500,
        )
        text = response.choices[0].message.content.strip()
        return json.loads(text)
    except Exception as e:
        logger.warning(f"LLM section analysis failed: {e}")
        return None


def analyze_scales(text_samples: list[dict], positions: list[dict]) -> dict | None:
    """Ask GPT to infer H/V scales from text samples.

    Returns {"h_scale": F, "v_scale": F} or None.
    """
    client = _get_client()
    if not client:
        return None

    prompt = (
        "From this CAD longitudinal profile, infer the horizontal and vertical scales.\n\n"
        f"Text samples with positions:\n{json.dumps(text_samples[:30], indent=2, ensure_ascii=False)}\n\n"
        "Respond with JSON: {\"h_scale\": number, \"v_scale\": number}"
    )

    try:
        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user", "content": prompt},
            ],
            timeout=10,
            max_tokens=200,
        )
        text = response.choices[0].message.content.strip()
        return json.loads(text)
    except Exception as e:
        logger.warning(f"LLM scale analysis failed: {e}")
        return None
