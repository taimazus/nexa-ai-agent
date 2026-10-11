import sys
import pytest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from ui.mascot import MascotState


def test_mascot_state_enum():
    assert MascotState.IDLE.value == "idle"
    assert MascotState.THINKING.value == "thinking"
    assert MascotState.WORKING.value == "working"
    assert MascotState.SPEAKING.value == "speaking"
    assert MascotState.SUCCESS.value == "success"
    assert MascotState.ERROR.value == "error"


def test_mascot_state_from_string():
    assert MascotState.from_string("thinking") == MascotState.THINKING
    assert MascotState.from_string("working") == MascotState.WORKING
    assert MascotState.from_string("unknown") == MascotState.IDLE
