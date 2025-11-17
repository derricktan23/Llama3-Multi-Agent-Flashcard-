import aiohttp
import json
import asyncio
import re


# ==========================================================
#  Helper: try to turn messy model output into valid JSON
# ==========================================================
def fix_and_parse_json(raw_text: str):
    print("[DEBUG] Attempting to parse JSON...")

    # Step 1: Try normal strict JSON parse
    try:
        return json.loads(raw_text), "strict"
    except Exception as e:
        print("[DEBUG] Strict parse failed:", e)

    # Step 2: Remove weird backticks, code fences, whitespace
    cleaned = raw_text.strip()
    cleaned = re.sub(r"```json|```", "", cleaned).strip()

    # Step 3: Remove trailing commas inside arrays/objects
    cleaned = re.sub(r",\s*([}\]])", r"\1", cleaned)

    # Step 4: Try again
    try:
        parsed = json.loads(cleaned)
        print("[DEBUG] JSON repaired successfully.")
        return parsed, "repaired"
    except Exception as e:
        print("[ERROR] JSON repair failed:", e)
        print("[ERROR] Raw model output was:")
        print(raw_text)
        return [], "failed"


# ==========================================================
#                   MAIN OLLAMA CALL
# ==========================================================
async def super_simple_ollama_flashcards(text: str) -> dict:
    url = "http://localhost:11434/api/generate"

    prompt = f"""
    Create exactly 5 technical interview flashcards about this topic: "{text}"

    You MUST return ONLY a JSON array, EXACTLY in this format:

    [
      {{"question": "What is X?", "answer": "Explanation..."}},
      {{"question": "How does Y work?", "answer": "Explanation..."}},
      {{"question": "Why use Z?", "answer": "Explanation..."}},
      {{"question": "What is W?", "answer": "Explanation..."}},
      {{"question": "Explain V", "answer": "Explanation..."}}
    ]

    RULES:
    - Each item MUST contain "question" and "answer".
    - No numbering (no Q1, A1).
    - No nested dictionaries.
    - No text before or after the JSON.
    - Do NOT wrap in code fences.
    """

    try:
        async with aiohttp.ClientSession(timeout=aiohttp.ClientTimeout(total=30)) as session:
            async with session.post(url, json={
                "model": "llama3.2:1b",
                "prompt": prompt,
                "stream": False,
                "options": {"temperature": 0.1}
            }) as response:

                if response.status == 200:
                    data = await response.json()
                    response_text = data['response']

                    parsed_json, mode = fix_and_parse_json(response_text)

                    return {
                        "final_raw_output": json.dumps(parsed_json, indent=2),
                        "parsed_cards": parsed_json,
                        "json_parse_mode": mode,
                        "method": "direct_ollama",
                        "status": "success"
                    }

                return {
                    "final_raw_output": json.dumps([{"question": "Error", "answer": "Ollama unavailable"}]),
                    "parsed_cards": [],
                    "json_parse_mode": "error",
                    "method": "error",
                    "status": "failed"
                }

    except Exception as e:
        return {
            "final_raw_output": json.dumps([{"question": "Error", "answer": str(e)}]),
            "parsed_cards": [],
            "json_parse_mode": "exception",
            "method": "exception",
            "status": "failed"
        }


# ==========================================================
#                   WRAPPER FUNCTION
# ==========================================================
async def generate_anki_cards(input_text: str) -> dict:
    print("[DEBUG] generate_anki_cards() called")
    print(f"[DEBUG] Input length: {len(input_text)} chars")

    result = await super_simple_ollama_flashcards(input_text)

    print("[DEBUG] super_simple_ollama_flashcards() returned keys:", list(result.keys()))
    print("[DEBUG] Raw output length:", len(result.get("final_raw_output", "")))
    print("[DEBUG] JSON parse mode:", result.get("json_parse_mode"))

    payload = {
        "final_raw_output": result["final_raw_output"],
        "parsed_cards": result["parsed_cards"],
        "topics_analyzed": input_text[:100],
        "review_status": "completed",
        "iterations_completed": 1,
        "method": result["method"],
        "json_parse_mode": result["json_parse_mode"],
    }

    print("[DEBUG] Final payload prepared.")
    return payload


# ==========================================================
#                   Local test
# ==========================================================
if __name__ == "__main__":
    r = asyncio.run(generate_anki_cards("prepare for java technical interview"))
    print("=== FINAL ===")
    print(json.dumps(r, indent=2))
