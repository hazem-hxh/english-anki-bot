"""
English Anki Bot - Translation (English -> Arabic)

Free, no API key needed. Tries GoogleTranslator first, falls back to
MyMemoryTranslator if Google fails (same order as the German bot).

WHY THERE ARE TWO BACKENDS:
GoogleTranslator (in the deep-translator library) works by scraping a
lightweight Google Translate page, not by calling a real API. Google has
started blocking that method with a CAPTCHA wall, so it often fails.
MyMemoryTranslator is a real free translation API, but it is a "translation
memory" lookup, so for unusual phrases it can occasionally return an
unrelated sentence. If you notice Google failing every time (slow replies),
you can flip the order in the tuple inside translate_sentence().

NEVER RETURNS AN EMPTY STRING:
If an Arabic field is empty, Anki silently skips the Arabic -> English card
(its front would be blank). So on total failure we return a visible
"[translation failed: ...]" marker instead, which guarantees both cards
are always created and the failure is easy to spot and fix by hand.

Requirements (installed on the host, not here):
    pip install deep-translator
"""

import time
from deep_translator import GoogleTranslator, MyMemoryTranslator
from concurrent.futures import ThreadPoolExecutor, TimeoutError as FutureTimeoutError

_executor = ThreadPoolExecutor(max_workers=2)

# Short pause before every call, to stay under free-tier rate limits when
# a long list is sent at once.
DELAY_BETWEEN_CALLS = 0.5  # seconds


def _call_google(english_sentence: str):
    return GoogleTranslator(source="en", target="ar").translate(english_sentence)


def _call_mymemory(english_sentence: str):
    # MyMemory wants locale-style codes. "ar-SA" is its code for Arabic.
    # (Not tested from here - if MyMemory ever errors about the language
    # code, check deep-translator's MyMemory language list.)
    return MyMemoryTranslator(source="en-GB", target="ar-SA").translate(english_sentence)


def _run_with_timeout(func, english_sentence: str, timeout_seconds: int):
    future = _executor.submit(func, english_sentence)
    return future.result(timeout=timeout_seconds)


def translate_sentence(english_sentence: str, timeout_seconds: int = 10) -> str:
    """Returns the Arabic translation of an English sentence.

    Tries Google, then MyMemory. If both fail, returns a non-empty marker
    string (see the note at the top of this file)."""
    time.sleep(DELAY_BETWEEN_CALLS)

    for name, func in (("Google", _call_google), ("MyMemory", _call_mymemory)):
        try:
            result = _run_with_timeout(func, english_sentence, timeout_seconds)
            if result and result.strip():
                return result
            print(f"{name} returned an empty translation for '{english_sentence}'")
        except FutureTimeoutError:
            print(f"{name} translation timed out for '{english_sentence}'")
        except Exception as e:
            print(f"{name} translation failed for '{english_sentence}': {e}")

    print(f"All translation backends failed for '{english_sentence}' - using fallback")
    return f"[translation failed: {english_sentence}]"
