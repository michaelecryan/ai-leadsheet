from __future__ import annotations

import tempfile
from pathlib import Path

from basic_pitch import ICASSP_2022_MODEL_PATH
from basic_pitch.inference import predict_and_save

from leadsheet.midi import ParsedMidi, load

SUPPORTED_EXTENSIONS = {".mp3", ".wav", ".flac", ".ogg", ".m4a"}


def load_audio(path: Path) -> ParsedMidi:
    """Transcribe an audio file to ParsedMidi via Basic Pitch."""
    with tempfile.TemporaryDirectory() as tmp:
        predict_and_save(
            [str(path)],
            tmp,
            save_midi=True,
            sonify_midi=False,
            save_model_outputs=False,
            save_notes=False,
            model_or_model_path=ICASSP_2022_MODEL_PATH,
        )
        midi_files = list(Path(tmp).glob("*.mid"))
        if not midi_files:
            raise RuntimeError("Basic Pitch did not produce a MIDI file.")
        return load(midi_files[0])
