"""
English Anki Bot - Packaging into .apkg (genanki)

Requirements (installed on the host, not here):
    pip install genanki

HOW DECK MATCHING WORKS (read this once):
Anki matches decks by their exact NAME when importing an .apkg. So to add a
new deck you never touch this file: just type the new deck's exact name in
the bot ("+ New deck"). The name is turned into a stable ID automatically.
The name you type must match your Anki deck EXACTLY (spelling and
capitalisation), or Anki will create a separate deck instead of adding to
your existing one.

EVERY SENTENCE BECOMES TWO CARDS:
  Card 1: English (+ audio) on the front  ->  Arabic on the back
  Card 2: Arabic on the front             ->  English (+ audio) on the back
"""

import hashlib
import genanki

# ---------------------------------------------------------------------------
# NOTE TYPE ID - READ BEFORE CHANGING
# Anki does NOT update an existing note type's fields/templates when you
# import a file whose note type has the same ID: it silently keeps the
# version already in your collection. So once you have imported cards,
# NEVER change MODEL_ID, and if you ever change the fields or templates
# below, you must also give the model a NEW ID (and a new name).
#
# This ID is deliberately different from the German bot's IDs, so the two
# bots' note types never collide inside the same Anki collection.
# ---------------------------------------------------------------------------
MODEL_ID = 1738204961

NOTE_MODEL = genanki.Model(
    MODEL_ID,
    "English-Arabic Sentence Model",
    fields=[
        {"name": "English"},
        {"name": "Arabic"},
        {"name": "Audio"},
    ],
    templates=[
        {
            "name": "English → Arabic",
            "qfmt": '<div class="english">{{English}}</div><div class="audio">{{Audio}}</div>',
            "afmt": '{{FrontSide}}<hr id="answer"><div class="arabic">{{Arabic}}</div>',
        },
        {
            "name": "Arabic → English",
            "qfmt": '<div class="arabic">{{Arabic}}</div>',
            "afmt": '{{FrontSide}}<hr id="answer">'
                    '<div class="english">{{English}}</div><div class="audio">{{Audio}}</div>',
        },
    ],
    # No fixed text colours on purpose: a hardcoded grey was nearly invisible
    # in Anki's dark mode on the German bot. Letting the text inherit the
    # theme colour works in both light and dark mode.
    css="""
.card {
    text-align: center;
    font-family: arial;
}
.english {
    font-size: 32px;
    font-weight: bold;
}
.arabic {
    direction: rtl;
    text-align: center;
    font-size: 34px;
    font-family: "Noto Naskh Arabic", "Traditional Arabic", "Geeza Pro", arial;
    line-height: 1.6;
}
.audio {
    margin-top: 10px;
}
""",
)


def _deck_id_for(deck_name: str) -> int:
    """Turns a deck name into a stable numeric ID (same name -> same ID,
    forever, including across bot restarts)."""
    digest = hashlib.sha256(deck_name.encode("utf-8")).hexdigest()
    return int(digest, 16) % (10 ** 10)


def build_package(deck_name: str, cards: list, output_path: str) -> str:
    """
    cards: list of dicts, each with keys:
        "english": str
        "arabic": str  (must never be empty - see translate.py)
        "audio_path": str (path to the mp3 from audio.py)

    Returns the path to the created .apkg file.
    """
    deck = genanki.Deck(_deck_id_for(deck_name), deck_name)
    media_files = []

    for card in cards:
        audio_filename = card["audio_path"].split("/")[-1]
        note = genanki.Note(
            model=NOTE_MODEL,
            fields=[
                card["english"],
                card["arabic"],
                f"[sound:{audio_filename}]",
            ],
        )
        deck.add_note(note)
        media_files.append(card["audio_path"])

    package = genanki.Package(deck)
    package.media_files = media_files
    package.write_to_file(output_path)
    return output_path
