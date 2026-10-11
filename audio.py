"""
English Anki Bot - Audio generation

Free, no API key needed. Uses Microsoft's edge-tts neural voices.

Requirements (installed on the host, not here):
    pip install edge-tts
"""

import hashlib
import asyncio
import edge_tts

# English-only voices (NOT the "Multilingual" ones). Lesson learned on the
# German bot: multilingual voices guess the language from the text, which
# goes wrong on short isolated words. English-only voices can't make that
# mistake. To switch, change ENGLISH_VOICE to one of these:
#   "en-US-JennyNeural"   <- female, American (current)
#   "en-US-AriaNeural"    <- female, American
#   "en-US-GuyNeural"     <- male, American
#   "en-GB-SoniaNeural"   <- female, British
#   "en-GB-RyanNeural"    <- male, British
# Voice names can change on Microsoft's side. If one stops working, run
# `edge-tts --list-voices` on the host to see what's currently available.
ENGLISH_VOICE = "en-US-JennyNeural"

# Negative = slower. "-10%" is a gentle slow-down for learners.
# Use "+0%" for normal speed or "-20%" for noticeably slower.
SPEECH_RATE = "-10%"


def _filename_for(sentence: str) -> str:
    """Turns a sentence into a short, safe, unique filename."""
    h = hashlib.sha1(sentence.encode("utf-8")).hexdigest()[:12]
    return f"audio_{h}.mp3"


async def generate_audio(sentence: str, output_dir: str = ".", timeout_seconds: int = 15) -> str:
    """Generates an mp3 for the given English sentence and returns its path.
    Raises TimeoutError if edge-tts doesn't answer in time, instead of
    hanging forever."""
    filename = _filename_for(sentence)
    path = f"{output_dir}/{filename}"
    communicate = edge_tts.Communicate(sentence, ENGLISH_VOICE, rate=SPEECH_RATE)
    await asyncio.wait_for(communicate.save(path), timeout=timeout_seconds)
    return path
