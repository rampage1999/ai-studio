"""
Artist Agent — generates images via ComfyUI on the bigbox RTX 5070 Ti.
Communicates through the nginx proxy at /comfy/.
"""

import json
import os
import urllib.request
import urllib.error
import uuid
from pathlib import Path
from datetime import datetime
from typing import Optional

COMFY_BASE = os.environ.get("COMFY_BASE_URL", "http://192.168.10.121/comfy")
OUTPUT_DIR = os.environ.get("STUDIO_DATA_DIR", "./projects")

SYSTEM_PROMPT = """You are the Artist Agent — a master of visual creation who brings stories to life through art.

Your expertise:
- Generating character portraits, scene illustrations, and concept art
- Translating written descriptions into vivid image prompts
- Suggesting visual styles, color palettes, and compositions
- Understanding different art styles: cinematic, anime, painterly, photorealistic, etc.

When given a task to create art, generate a detailed, well-structured prompt
that captures the essence of what needs to be visualized. Return your prompt
clearly labeled so the system can send it to the image generation engine.

Always consider:
- The project's genre and tone (dark fantasy needs different treatment than sci-fi)
- Character descriptions from the Bible
- Location descriptions from the Bible
- The right visual style for the moment"""


def _build_sdxl_workflow(prompt: str, negative_prompt: str, model: str,
                          width: int, height: int, seed: int, steps: int,
                          cfg: float) -> dict:
    """Build an API-format SDXL txt2img workflow JSON."""
    prompt = prompt.replace('"', "'")
    negative_prompt = negative_prompt.replace('"', "'")

    return {
        "3": {
            "class_type": "KSampler",
            "inputs": {
                "seed": seed if seed > 0 else int(uuid.uuid4().int % (2**63)),
                "steps": steps,
                "cfg": cfg,
                "sampler_name": "dpmpp_2m",
                "scheduler": "karras",
                "denoise": 1.0,
                "model": ["4", 0],
                "positive": ["6", 0],
                "negative": ["7", 0],
                "latent_image": ["5", 0]
            }
        },
        "4": {
            "class_type": "CheckpointLoaderSimple",
            "inputs": {"ckpt_name": model}
        },
        "5": {
            "class_type": "EmptyLatentImage",
            "inputs": {"width": width, "height": height, "batch_size": 1}
        },
        "6": {
            "class_type": "CLIPTextEncode",
            "inputs": {"text": prompt, "clip": ["4", 1]}
        },
        "7": {
            "class_type": "CLIPTextEncode",
            "inputs": {"text": negative_prompt, "clip": ["4", 1]}
        },
        "8": {
            "class_type": "VAEDecode",
            "inputs": {"samples": ["3", 0], "vae": ["4", 2]}
        },
        "9": {
            "class_type": "SaveImage",
            "inputs": {
                "filename_prefix": "ai_studio_",
                "images": ["8", 0]
            }
        }
    }


def list_models() -> list[str]:
    """Fetch available checkpoints from ComfyUI."""
    try:
        req = urllib.request.Request(f"{COMFY_BASE}/api/object_info/CheckpointLoaderSimple")
        resp = urllib.request.urlopen(req, timeout=10)
        data = json.loads(resp.read())
        ckpt_info = data.get("CheckpointLoaderSimple", {})
        ckpt_names = ckpt_info.get("input", {}).get("required", {}).get("ckpt_name", [])
        models = []
        for entry in ckpt_names:
            if isinstance(entry, list):
                models.extend(name for name in entry if isinstance(name, str))
        return models
    except Exception as e:
        print(f"  [Artist] list_models error: {e}")
        return []


def generate_image(
    prompt: str,
    negative_prompt: str = "",
    model: str = "dreamShaper.safetensors",
    width: int = 1024,
    height: int = 1024,
    seed: int = -1,
    steps: int = 25,
    cfg: float = 7.0,
    project_name: str = "",
    timeout: int = 120,
) -> dict:
    """
    Send a prompt to ComfyUI via nginx proxy, wait for completion,
    download the output image, and return result info.
    """
    client_id = str(uuid.uuid4())

    workflow = _build_sdxl_workflow(
        prompt=prompt,
        negative_prompt=negative_prompt,
        model=model,
        width=width,
        height=height,
        seed=seed,
        steps=steps,
        cfg=cfg,
    )

    payload = json.dumps({
        "prompt": workflow,
        "client_id": client_id,
    }).encode()

    # Submit
    submit_url = f"{COMFY_BASE}/prompt"
    print(f"  [Artist] Submitting to ComfyUI at {submit_url}")
    print(f"  [Artist] Model: {model}, Prompt: {prompt[:80]}...")
    print(f"  [Artist] Size: {width}x{height}, Steps: {steps}, CFG: {cfg}")

    try:
        req = urllib.request.Request(submit_url, data=payload,
                                     headers={"Content-Type": "application/json"})
        resp = urllib.request.urlopen(req, timeout=30)
        result = json.loads(resp.read())
    except urllib.error.HTTPError as e:
        body = e.read().decode()[:500]
        return {"error": f"ComfyUI submit failed: HTTP {e.code}", "detail": body}
    except Exception as e:
        return {"error": f"ComfyUI submit failed: {e}"}

    prompt_id = result.get("prompt_id")
    if not prompt_id:
        return {"error": "No prompt_id returned", "detail": result}

    node_errors = result.get("node_errors", {})
    if node_errors:
        print(f"  [Artist] Node errors: {json.dumps(node_errors, indent=2)}")

    print(f"  [Artist] Prompt ID: {prompt_id}")
    print(f"  [Artist] Waiting for completion...")

    # Poll history until done
    poll_url = f"{COMFY_BASE}/history/{prompt_id}"
    deadline = datetime.now().timestamp() + timeout

    while datetime.now().timestamp() < deadline:
        import time
        time.sleep(2)

        try:
            req = urllib.request.Request(poll_url)
            resp = urllib.request.urlopen(req, timeout=10)
            data = json.loads(resp.read())
        except urllib.error.HTTPError as e:
            if e.code == 404:
                continue
            return {"error": f"Poll failed: HTTP {e.code}"}
        except Exception as e:
            return {"error": f"Poll failed: {e}"}

        entry = data.get(prompt_id, {})
        if not entry:
            continue

        status = entry.get("status", {})
        completed = status.get("completed", False)

        if status.get("status_str") == "error":
            msgs = status.get("messages", [])
            error_detail = ""
            for mtype, mdata in msgs:
                if mtype == "execution_error":
                    error_detail = mdata.get("exception_message", "")
            return {"error": "Execution failed", "detail": error_detail, "messages": msgs}

        if completed:
            outputs = entry.get("outputs", {})
            images = []
            for node_id, node_out in outputs.items():
                for img in node_out.get("images", []):
                    images.append(img)

            if not images:
                return {"error": "No images in output", "outputs": outputs}

            # Download the first image
            img = images[0]
            filename = img.get("filename", "")
            subfolder = img.get("subfolder", "")
            img_type = img.get("type", "output")

            view_url = f"{COMFY_BASE}/view?filename={filename}&subfolder={subfolder}&type={img_type}"
            print(f"  [Artist] Downloading: {view_url}")

            try:
                req = urllib.request.Request(view_url)
                img_resp = urllib.request.urlopen(req, timeout=30)
                img_data = img_resp.read()
            except Exception as e:
                return {"error": f"Download failed: {e}", "images": images}

            # Save to project images dir
            if project_name:
                save_dir = Path(OUTPUT_DIR) / project_name / "images"
            else:
                save_dir = Path(OUTPUT_DIR) / "_generated"

            save_dir.mkdir(parents=True, exist_ok=True)

            # Unique filename
            ts = datetime.now().strftime("%Y%m%d_%H%M%S")
            local_filename = f"comfy_{ts}_{filename}"
            local_path = save_dir / local_filename

            with open(local_path, "wb") as f:
                f.write(img_data)

            print(f"  [Artist] Saved: {local_path} ({len(img_data)} bytes)")

            return {
                "success": True,
                "prompt_id": prompt_id,
                "image_url": f"/studio/api/projects/{project_name}/images/{local_filename}",
                "local_path": str(local_path),
                "size_bytes": len(img_data),
                "seed": workflow["3"]["inputs"]["seed"],
                "model": model,
                "filename": local_filename,
                "generated_images_entry": {
                    "filename": local_filename,
                    "prompt": prompt,
                    "negative_prompt": negative_prompt,
                    "seed": workflow["3"]["inputs"]["seed"],
                    "model": model,
                    "steps": steps,
                    "cfg": cfg,
                    "created": datetime.utcnow().isoformat(),
                    "node_prompt_id": prompt_id,
                },
            }

    return {"error": f"Timeout after {timeout}s"}


class ArtistAgent:
    """Agent that generates images via ComfyUI."""

    def __init__(self):
        pass

    async def execute(self, task: str, project_name: str, messages: list[dict]) -> str:
        """
        Execute an art generation task. The task string should contain:
        - The visual description/prompt
        - Optional parameters (model, size, style)
        """
        # Parse task for optional parameters
        import re

        # Defaults
        prompt_text = task
        negative = "worst quality, low quality, blurry, distorted, ugly, deformed"
        model = "dreamShaper.safetensors"
        width, height = 1024, 1024
        steps = 25
        cfg = 7.0

        # Extract model hint if present
        model_match = re.search(r'--model\s+([\w\.-]+\.safetensors)', task)
        if model_match:
            model = model_match.group(1)
            prompt_text = re.sub(r'--model\s+[\w\.-]+\.safetensors', '', prompt_text).strip()

        # Extract size hint
        size_match = re.search(r'--size\s+(\d+)x(\d+)', task)
        if size_match:
            width, height = int(size_match.group(1)), int(size_match.group(2))
            prompt_text = re.sub(r'--size\s+\d+x\d+', '', prompt_text).strip()

        # Extract steps hint
        steps_match = re.search(r'--steps\s+(\d+)', task)
        if steps_match:
            steps = int(steps_match.group(1))
            prompt_text = re.sub(r'--steps\s+\d+', '', prompt_text).strip()

        # Do the generation
        result = generate_image(
            prompt=prompt_text,
            negative_prompt=negative,
            model=model,
            width=width,
            height=height,
            seed=-1,
            steps=steps,
            cfg=cfg,
            project_name=project_name,
        )

        if "error" in result:
            return f"[Artist Agent — ERROR]\n{result['error']}\n{result.get('detail', '')}"

        return (
            f"[Artist Agent — Image Generated]\n\n"
            f"Model: {result['model']}\n"
            f"Seed: {result['seed']}\n"
            f"Size: {width}x{height}\n"
            f"File: {result['local_path']}\n"
            f"Size: {result['size_bytes']:,} bytes\n"
            f"Open: http://192.168.10.121/studio/api/projects/{project_name}/images/{result['filename']}"
        )
