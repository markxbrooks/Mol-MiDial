"""
Dial Settings
"""

from molmidial.midi.dial.range import DialRange


class DialSettings:
    """Settings for UI dials controlling camera behavior."""

    ZOOM = DialRange(min=-320, init=-130, max=100)

    ROT_X = DialRange(min=0, init=0, max=360)
    ROT_Y = DialRange(min=0, init=0, max=360)
    ROT_Z = DialRange(min=0, init=0, max=360)

    TRANSLATE_X = DialRange(min=-60, init=0, max=60)
    TRANSLATE_Y = DialRange(min=-60, init=0, max=60)

    FOG_DENSITY = DialRange(min=0.0, init=0.1, max=0.3)
    FOG_NEAR = DialRange(min=30, init=70, max=100)
    FOG_FAR = DialRange(min=70, init=100, max=200)

    # Clipping plane settings
    CLIP_Z = DialRange(min=-100, init=20, max=100)
    CLIP_DEPTH = DialRange(min=1.0, init=50.0, max=100.0)

    @staticmethod
    def get_zoom_range() -> tuple[int, int]:
        return DialSettings.ZOOM.min, DialSettings.ZOOM.max
