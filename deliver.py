"""
English Anki Bot - Pipeline: translate + audio + package

Ties the other modules together:
    translate.py  -> Arabic meaning of each English sentence
    audio.py      -> English mp3 for each sentence
    packaging.py  -> combines them into a .apkg for the chosen deck

bot.py then sends the finished file back in Telegram.
"""

import os
import tempfile
import asyncio
import logging

import translate
import audio
import packaging

logger = logging.getLogger(__name__)


async def process_sentences_and_get_file(
    profile: str, deck: str, sentence_items: list, progress_callback=None
) -> str:
    """
    Runs the full pipeline for a batch of English sentences.

    sentence_items: list of dicts, each with:
        "sentence": str (required) - the English sentence
        "translation": str or None - your own Arabic translation; if given,
                       auto-translation is skipped for that sentence

    progress_callback: optional async function called as
        progress_callback(current_index, total) after each sentence
        finishes (1-based). Lets bot.py show "Processing 3 of 10..."
        without this module knowing anything about Telegram.

    Returns the path to the finished .apkg file.
    """
    work_dir = tempfile.mkdtemp(prefix="anki_batch_")
    cards = []
    total = len(sentence_items)

    for i, item in enumerate(sentence_items, start=1):
        sentence = item["sentence"]
        manual_translation = item.get("translation")

        if manual_translation:
            arabic = manual_translation
            logger.info(f"Using provided translation for: {sentence}")
        else:
            logger.info(f"Translating: {sentence}")
            # translate_sentence is a blocking network call: run it in a
            # background thread so a slow call can't freeze the whole bot.
            arabic = await asyncio.to_thread(translate.translate_sentence, sentence)
            logger.info(f"Translated to: {arabic}")

        logger.info(f"Generating audio for: {sentence}")
        audio_path = await audio.generate_audio(sentence, output_dir=work_dir)
        logger.info(f"Audio saved to: {audio_path}")

        cards.append({
            "english": sentence,
            "arabic": arabic,
            "audio_path": audio_path,
        })

        if progress_callback:
            await progress_callback(i, total)

    output_path = os.path.join(work_dir, f"{deck.replace(' ', '_')}.apkg")
    logger.info("Packaging .apkg...")
    # build_package is blocking (disk I/O) too, so same reasoning.
    await asyncio.to_thread(packaging.build_package, deck, cards, output_path)
    logger.info("Packaging done.")
    return output_path
