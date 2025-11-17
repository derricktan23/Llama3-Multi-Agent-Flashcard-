import streamlit as st
import requests
import json
import os

BACKEND_URL = os.getenv("BACKEND_URL", "http://localhost:8000")

# ---------------------------------------------------------
# Page Config
# ---------------------------------------------------------
st.set_page_config(
    page_title="Flashcard Generator",
    page_icon="📚",
    layout="wide"
)

# ---------------------------------------------------------
# CSS Styles
# ---------------------------------------------------------
st.markdown("""
<style>
    .flashcard {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        color: white;
        padding: 1.5rem;
        border-radius: 10px;
        margin: 1rem 0;
        box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
    }
    .flashcard-question {
        font-size: 1.2rem;
        font-weight: bold;
        margin-bottom: 1rem;
    }
    .flashcard-answer {
        font-size: 1rem;
        background: rgba(255, 255, 255, 0.1);
        padding: 0.8rem;
        border-radius: 5px;
    }
    .debug-log {
        background: #f8f9fa;
        border-left: 4px solid #007bff;
        padding: 0.5rem;
        margin: 0.2rem 0;
        font-family: monospace;
        font-size: 0.8rem;
    }
    .debug-error {
        background: #f8d7da;
        border-left: 4px solid #dc3545;
        padding: 0.5rem;
        margin: 0.2rem 0;
        font-family: monospace;
        font-size: 0.8rem;
    }
    .debug-success {
        background: #d1ecf1;
        border-left: 4px solid #28a745;
        padding: 0.5rem;
        margin: 0.2rem 0;
        font-family: monospace;
        font-size: 0.8rem;
    }
</style>
""", unsafe_allow_html=True)


# ---------------------------------------------------------
# Session State Init
# ---------------------------------------------------------
if "flashcards" not in st.session_state:
    st.session_state.flashcards = None
if "debug_logs" not in st.session_state:
    st.session_state.debug_logs = []
if "last_response" not in st.session_state:
    st.session_state.last_response = None


# ---------------------------------------------------------
# Debug Logging Utility
# ---------------------------------------------------------
def log_debug(message, level="info"):
    import datetime
    ts = datetime.datetime.now().strftime("%H:%M:%S")
    st.session_state.debug_logs.append({"message": f"[{ts}] {message}", "level": level})
    st.session_state.debug_logs = st.session_state.debug_logs[-50:]  # Keep last 50


# ---------------------------------------------------------
# Backend Request
# ---------------------------------------------------------
def generate_flashcards_simple(text: str):
    try:
        log_debug("🚀 Sending request to backend")

        response = requests.post(
            f"{BACKEND_URL}/generate-flashcards-sync",
            json={"text": text},
            timeout=300
        )

        log_debug(f"📥 Backend status: {response.status_code}")

        response.raise_for_status()
        result = response.json()

        st.session_state.last_response = result
        return result

    except Exception as e:
        log_debug(f"❌ Backend error: {e}", "error")
        st.error("Backend request failed")
        return None


# ---------------------------------------------------------
# JSON Parsing
# ---------------------------------------------------------
def parse_json_cards(raw_output: str):
    """Extract and parse JSON array containing cards."""
    try:
        cleaned = raw_output.strip()

        # Remove code fences if present
        cleaned = cleaned.replace("```json", "").replace("```", "").strip()

        # Extract JSON array
        start = cleaned.find("[")
        end = cleaned.rfind("]")

        if start == -1 or end == -1:
            log_debug("❌ JSON array not found", "error")
            return []

        cleaned = cleaned[start:end + 1]
        cards = json.loads(cleaned)

        if isinstance(cards, list):
            log_debug(f"🎉 Parsed {len(cards)} cards successfully", "success")
            return cards

        return []

    except Exception as e:
        log_debug(f"❌ JSON parsing failed: {e}", "error")
        return []


# ---------------------------------------------------------
# Main Parse Entry
# ---------------------------------------------------------
def parse_cards(result_data):
    if not result_data:
        return []

    # Unified response shape
    raw_output = (
        result_data.get("flashcards", {}).get("final_raw_output") or
        result_data.get("final_raw_output")
    )

    if not raw_output:
        log_debug("❌ No raw_output found in response", "error")
        return []

    return parse_json_cards(raw_output)


# ---------------------------------------------------------
# Display Flashcards
# ---------------------------------------------------------
def display_cards(cards):
    if not cards:
        st.warning("No flashcards were generated.")
        return

    st.success(f"Generated {len(cards)} flashcards!")

    for card in cards:
        question = card.get("question", "No question")
        answer = card.get("answer", "No answer")

        st.markdown(f"""
            <div class="flashcard">
                <div class="flashcard-question">Q: {question}</div>
                <div class="flashcard-answer">A: {answer}</div>
            </div>
        """, unsafe_allow_html=True)


# ---------------------------------------------------------
# Debug Log Viewer
# ---------------------------------------------------------
def display_debug_logs():
    with st.expander("🐛 Debug Logs", expanded=True):
        if st.button("Clear Logs"):
            st.session_state.debug_logs = []
            st.session_state.last_response = None
            st.session_state.flashcards = None
            st.rerun()

        for log in st.session_state.debug_logs:
            level = log["level"]
            css = {
                "error": "debug-error",
                "success": "debug-success"
            }.get(level, "debug-log")

            st.markdown(f"<div class='{css}'>{log['message']}</div>", unsafe_allow_html=True)


# ---------------------------------------------------------
# Backend Health Check
# ---------------------------------------------------------
def check_backend():
    try:
        res = requests.get(f"{BACKEND_URL}/health", timeout=4)
        return res.status_code == 200
    except:
        return False


# ---------------------------------------------------------
# Main App
# ---------------------------------------------------------
def main():
    st.title("🤖 Flashcard Generator")

    display_debug_logs()

    if not check_backend():
        st.error("Backend not available! Start FastAPI on port 8000.")
        return

    st.subheader("📝 Input Text")
    text = st.text_area("Enter text:", height=160)

    col1, col2 = st.columns(2)

    with col1:
        if st.button("🚀 Generate Flashcards", type="primary", use_container_width=True):
            if text.strip():
                result = generate_flashcards_simple(text)
                cards = parse_cards(result)
                st.session_state.flashcards = cards
                st.rerun()

    with col2:
        if st.session_state.flashcards is not None:
            if st.button("🗑️ Clear Results", use_container_width=True):
                st.session_state.flashcards = None
                st.session_state.last_response = None
                st.session_state.debug_logs = []
                st.rerun()

    if st.session_state.flashcards is not None:
        st.markdown("---")
        st.subheader("🎴 Generated Flashcards")
        display_cards(st.session_state.flashcards)

        with st.expander("🔍 Raw API Response"):
            st.json(st.session_state.last_response)


if __name__ == "__main__":
    main()
