"""Physical segment displays."""
from collections import namedtuple
from operator import attrgetter
from typing import List, Optional

from mpf.core.device_monitor import DeviceMonitor
from mpf.core.placeholder_manager import TextTemplate
from mpf.core.system_wide_device import SystemWideDevice
from mpf.platforms.interfaces.segment_display_platform_interface import FlashingType

MYPY = False
if MYPY:   # pragma: no cover
    from mpf.platforms.interfaces.segment_display_platform_interface import SegmentDisplayPlatformInterface     # pylint: disable-msg=cyclic-import,unused-import; # noqa
    from mpf.core.platform import SegmentDisplayPlatform    # pylint: disable-msg=cyclic-import,unused-import; # noqa

TextStack = namedtuple("TextStack", ["text", "platform_options", "priority", "key"])


@DeviceMonitor("text")
class SegmentDisplay(SystemWideDevice):

    """A physical segment display in a pinball machine."""

    config_section = 'segment_displays'
    collection = 'segment_displays'
    class_label = 'segment_display'

    def __init__(self, machine, name: str) -> None:
        """Initialise segment display device."""
        super().__init__(machine, name)
        self.hw_display = None                  # type: Optional[SegmentDisplayPlatformInterface]
        self.platform = None                    # type: Optional[SegmentDisplayPlatform]
        self._text_stack = []                   # type: List[TextStack]
        self._current_placeholder = None        # type: Optional[TextTemplate]
        self.text = ""                          # type: Optional[str]
        self.flashing = FlashingType.NO_FLASH   # type: FlashingType
        self.platform_settings = None           # type: Optional[dict]

    async def _initialize(self):
        await super()._initialize()
        """Initialise display."""
        # load platform
        self.platform = self.machine.get_platform_sections('segment_displays', self.config['platform'])
        self.platform.assert_has_feature("segment_displays")

        if not self.platform.features['allow_empty_numbers'] and self.config['number'] is None:
            self.raise_config_error("Segment Display must have a number.", 1)

        # configure hardware
        try:
            self.hw_display = await self.platform.configure_segment_display(self.config['number'],
                                                                            self.config['platform_settings'])
        except AssertionError as e:
            raise AssertionError("Error in platform while configuring segment display {}. "
                                 "See error above.".format(self.name)) from e

    def validate_and_parse_config(self, config: dict, is_mode_config: bool, debug_prefix: str = None) -> dict:
        """Return the parsed and validated config.

        Args:
        ----
            config: Config of device
            is_mode_config: Whether this device is loaded in a mode or system-wide
            debug_prefix: Prefix to use when logging.

        Returns: Validated config
        """
        config = super().validate_and_parse_config(config, is_mode_config, debug_prefix)
        platform = self.machine.get_platform_sections('segment_displays', getattr(config, "platform", None))
        platform.assert_has_feature("segment_displays")
        config['platform_settings'] = platform.validate_segment_display_section(self,
                                                                                config.get('platform_settings', None))
        return config

    def add_text(self, text: str, platform_options: dict = None, priority: int = 0, key: str = None) -> None:
        """Add text to display stack.

        This will replace texts with the same key.
        """
        # remove old text in case it has the same key
        self._text_stack[:] = [x for x in self._text_stack if x.key != key]
        # add new text
        self._text_stack.append(TextStack(text, platform_options, priority, key))
        self._update_stack()

    def set_flashing(self, flashing: FlashingType):
        """Enable/Disable flashing."""
        self.flashing = flashing
        # invalidate text to force an update
        self.text = None
        self._update_display()

    def remove_text_by_key(self, key: str):
        """Remove entry from text stack."""
        self._text_stack[:] = [x for x in self._text_stack if x.key != key]
        self._update_stack()

    def _update_stack(self) -> None:
        """Sort stack and show top entry on display."""
        # do nothing if stack is emtpy. set display empty
        assert self.hw_display is not None
        if not self._text_stack:
            self.hw_display.set_text("", flashing=FlashingType.NO_FLASH)
            if self._current_placeholder:
                self.text = ""
                self._current_placeholder = None
            return

        # sort stack by priority
        self._text_stack.sort(key=attrgetter("priority"), reverse=True)
        # get top entry
        top_entry = self._text_stack[0]

        self._current_placeholder = TextTemplate(self.machine, top_entry.text)
        self.platform_options = top_entry.platform_options
        self._update_display()

    def _update_display(self, *args, **kwargs) -> None:
        """Update display to current text."""
        del args
        del kwargs
        assert self.hw_display is not None
        if not self._current_placeholder:
            new_text = ""
        else:
            new_text, future = self._current_placeholder.evaluate_and_subscribe({})
            future.add_done_callback(self._update_display)

        # set text to display if it changed
        if new_text != self.text:
            self.text = new_text
            self.hw_display.set_text(self.text, flashing=self.flashing, platform_options=self.platform_options)
