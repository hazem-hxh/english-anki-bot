"""
English Anki Bot - Audio generation

Free, no API key needed. Uses Microsoft's edge-tts neural voices.

Requirements (installed on the host, not here):
    pip install edge-tts
"""

import hashlib
import asyncio
import edge_tts
from importlib.metadata import version, PackageNotFoundError

try:
    EDGE_TTS_VERSION = version("edge-tts")
except PackageNotFoundError:
    EDGE_TTS_VERSION = "unknown"
# Printed once at startup so the Railway logs show which version is really running.
print(f"edge-tts version installed: {EDGE_TTS_VERSION}")

# English-only voices (NOT the "Multilingual" ones). Lesson learned on the
# German bot: multilingual voices guess the language from the text, which
# goes wrong on short isolated words. English-only voices can't make that
# mistake. To switch, change ENGLISH_VOICE to one of these:
#   "en-US-AvaNeural"     <- female, American (current)
#   "en-US-JennyNeural"   <- female, American (previous default)
#   "en-US-AndrewNeural"  <- male, American
#   "en-US-BrianNeural"   <- male, American
#   "en-US-AriaNeural"    <- female, American
#   "en-US-GuyNeural"     <- male, American
#   "en-GB-SoniaNeural"   <- female, British
#   "en-GB-RyanNeural"    <- male, British
# Voice names can change on Microsoft's side. If one stops working, run
# `edge-tts --list-voices` on the host to see what's currently available.
ENGLISH_VOICE = "en-US-AvaNeural"

# Negative = slower. "-40%" is a slow pace suited to beginners.
# Going slower than about "-50%" starts to sound unnatural and robotic.
# Use "+0%" for normal speed, "-25%" for a moderate slow-down.
SPEECH_RATE = "-40%"


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
    try:
        await asyncio.wait_for(communicate.save(path), timeout=timeout_seconds)
    except Exception as e:
        # Add the installed version so the error shown in Telegram tells us
        # whether the latest edge-tts is really the one running.
        raise RuntimeError(f"{e} [edge-tts {EDGE_TTS_VERSION}]") from e
    return path
