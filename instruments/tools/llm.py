"""Thin Gemini (Vertex AI) client with structured output and an on-disk cache.

Auth is Application Default Credentials (`gcloud auth application-default
login`). Responses are cached under instruments/.cache keyed by
(model, prompt, schema), so re-running a QA report is free and returns
identical results; delete the cache to force fresh calls.
"""

import hashlib
import json
from pathlib import Path

import yaml
from google import genai
from google.genai import types

ROOT = Path(__file__).resolve().parents[1]
CACHE = ROOT / ".cache" / "llm"
CONFIG = yaml.safe_load((ROOT / "qa_config.yaml").read_text())

_client = None


def client():
    global _client
    if _client is None:
        v = CONFIG["vertex"]
        _client = genai.Client(vertexai=True, project=v["project"], location=v["location"])
    return _client


def ask_json(task, prompt, schema, images=()):
    """Run `prompt` against the model configured for `task`; return (parsed, meta).

    `images` is a sequence of (bytes, mime_type) pairs sent before the prompt.
    """
    model = CONFIG["models"][task]
    key_src = json.dumps(
        [model, prompt, schema, [hashlib.sha256(b).hexdigest() for b, _ in images]],
        sort_keys=True, ensure_ascii=False,
    )
    key = hashlib.sha256(key_src.encode()).hexdigest()
    path = CACHE / f"{key}.json"
    if path.exists():
        hit = json.loads(path.read_text())
        return hit["parsed"], hit["meta"]

    parts = [types.Part.from_bytes(data=b, mime_type=m) for b, m in images] + [prompt]
    resp = client().models.generate_content(
        model=model,
        contents=parts,
        config=types.GenerateContentConfig(
            temperature=CONFIG["temperature"],
            response_mime_type="application/json",
            response_schema=schema,
        ),
    )
    parsed = json.loads(resp.text)
    usage = resp.usage_metadata
    meta = {
        "model": model,
        "model_version": resp.model_version,
        "input_tokens": usage.prompt_token_count,
        "output_tokens": usage.candidates_token_count,
    }
    CACHE.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps({"parsed": parsed, "meta": meta}, ensure_ascii=False))
    return parsed, meta
