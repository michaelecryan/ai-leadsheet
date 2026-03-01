"""Audio transcription — converts an audio file to ParsedMidi via Basic Pitch."""

from __future__ import annotations

import sys
import tempfile
import types
from pathlib import Path

# resampy 0.4.x uses pkg_resources which was removed from setuptools 81+.
# Inject a minimal shim before basic_pitch imports resampy.
if "pkg_resources" not in sys.modules:
    def _resource_filename(pkg, fname):
        import importlib
        mod = importlib.import_module(pkg) if isinstance(pkg, str) else pkg
        return str(Path(mod.__file__).parent / fname)
    _shim = types.ModuleType("pkg_resources")
    _shim.resource_filename = _resource_filename  # type: ignore[attr-defined]
    sys.modules["pkg_resources"] = _shim

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
