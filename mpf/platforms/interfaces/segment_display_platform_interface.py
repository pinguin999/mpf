"""Support for physical segment displays."""
import abc
from typing import Any, Optional
from enum import Enum


class FlashingType(Enum):

    """Determine how a segment display should flash."""

    NO_FLASH = False
    FLASH_ALL = True
    FLASH_MATCH = "match"


class SegmentDisplayPlatformInterface(metaclass=abc.ABCMeta):

    """Interface for a segment display in hardware platforms."""

    __slots__ = ["number"]

    def __init__(self, number: Any) -> None:
        """Remember the number."""
        self.number = number

    @classmethod
    def get_segment_display_config_section(cls) -> Optional[str]:
        """Return addition config section for segment displays."""
        return None

    def validate_segment_display_section(self, segment_display, config) -> dict:
        """Validate segment display config for platform."""
        if self.get_segment_display_config_section():
            spec = self.get_segment_display_config_section()   # pylint: disable-msg=assignment-from-none
            config = segment_display.machine.config_validator.validate_config(spec, config, segment_display.name)
        elif config:
            raise AssertionError("No platform_config supported but not empty {} for segment display {}".
                                 format(config, segment_display.name))

        return config

    @abc.abstractmethod
    def set_text(self, text: str, flashing: FlashingType, platform_options: dict = None) -> None:
        """Set a text to the display.

        This text will be right aligned in case the text is shorter than the display.
        If it is too long it will be cropped on the left.
        """
        raise NotImplementedError


class SegmentDisplaySoftwareFlashPlatformInterface(SegmentDisplayPlatformInterface):

    """SegmentDisplayPlatformInterface with software emulation for flashing."""

    __slots__ = ["_flash_on", "_flashing", "_text"]

    def __init__(self, number: Any) -> None:
        """Remember the number."""
        super().__init__(number)
        self._flash_on = True
        self._flashing = FlashingType.NO_FLASH      # type: FlashingType
        self._text = ""

    def set_software_flash(self, state):
        """Set software flashing state."""
        self._flash_on = state

        if self._flashing == FlashingType.NO_FLASH:
            return

        # do not flash empty text
        if not self._text:
            return

        if state:
            self._set_text(self._text)
        else:
            if self._flashing == FlashingType.FLASH_MATCH:
                # blank the last two chars
                self._set_text(self._text[0:-2] + "  ")
            else:
                self._set_text("")

    def set_text(self, text: str, flashing: FlashingType, platform_options: dict = None) -> None:
        """Set a text to the display."""
        self._text = text
        self._flashing = flashing
        if flashing == FlashingType.NO_FLASH:
            self._flash_on = True
        if flashing == FlashingType.NO_FLASH or self._flash_on or not text:
            self._set_text(text)

    @abc.abstractmethod
    def _set_text(self, text: str) -> None:
        """Set a text to the display."""
        raise NotImplementedError
