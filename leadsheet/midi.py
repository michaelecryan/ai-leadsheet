from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path

import mido


@dataclass
class Note:
    pitch: int          # MIDI note number (0–127)
    start_beat: float   # position in beats from song start
    duration_beat: float
    velocity: int       # 0–127
    channel: int        # MIDI channel (0–15)


@dataclass
class ParsedMidi:
    ticks_per_beat: int
    tempo: int                  # microseconds per beat (500_000 = 120 BPM)
    time_sig_numerator: int
    time_sig_denominator: int
    notes: list[Note] = field(default_factory=list)

    @property
    def bpm(self) -> float:
        return 60_000_000 / self.tempo

    @property
    def beats_per_measure(self) -> int:
        return self.time_sig_numerator


def load(path: str | Path) -> ParsedMidi:
    """Parse a MIDI file and return a ParsedMidi with all notes in beat units."""
    mid = mido.MidiFile(str(path))
    tpb = mid.ticks_per_beat

    # Defaults (MIDI spec)
    tempo = 500_000
    time_sig_num = 4
    time_sig_den = 4
    notes: list[Note] = []

    # Single pass over all tracks: collect meta messages and notes together
    for track in mid.tracks:
        active: dict[int, tuple[int, int, int]] = {}  # pitch -> (start_tick, velocity, channel)
        tick = 0

        for msg in track:
            tick += msg.time

            if msg.type == "set_tempo":
                tempo = msg.tempo
            elif msg.type == "time_signature":
                time_sig_num = msg.numerator
                time_sig_den = msg.denominator
            elif msg.type == "note_on" and msg.velocity > 0:
                active[msg.note] = (tick, msg.velocity, msg.channel)
            elif msg.type == "note_off" or (msg.type == "note_on" and msg.velocity == 0):
                if msg.note in active:
                    start_tick, velocity, channel = active.pop(msg.note)
                    notes.append(Note(
                        pitch=msg.note,
                        start_beat=start_tick / tpb,
                        duration_beat=(tick - start_tick) / tpb,
                        velocity=velocity,
                        channel=channel,
                    ))

    notes.sort(key=lambda n: n.start_beat)
    return ParsedMidi(
        ticks_per_beat=tpb,
        tempo=tempo,
        time_sig_numerator=time_sig_num,
        time_sig_denominator=time_sig_den,
        notes=notes,
    )
