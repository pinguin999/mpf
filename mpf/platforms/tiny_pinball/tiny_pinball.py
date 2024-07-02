import asyncio
from typing import Optional, List, Dict

from mpf.platforms.interfaces.driver_platform_interface import DriverPlatformInterface, PulseSettings, HoldSettings

from mpf.platforms.interfaces.switch_platform_interface import SwitchPlatformInterface

from mpf.platforms.tiny_pinball.software_controller import SoftwareController, UnknownDestination

from mpf.core.logging import LogMixin
from mpf.core.utility_functions import Util

from mpf.core.platform import (
    SwitchPlatform,
    DriverPlatform,
    SwitchSettings,
    DriverSettings,
    DriverConfig,
    SwitchConfig,
    RepulseSettings,
)


class TinyPinballSwitch(SwitchPlatformInterface):

    """A switch in the TINYPINBALL platform."""

    def get_board_name(self):
        """Return board name."""
        return "TINYPINBALL"


class TinyPinballDriver(DriverPlatformInterface):

    """A driver in the TINYPINBALL platform."""

    __slots__ = ["platform", "_pulse_ms", "_recycle_time", "index"]  # type: List[str]

    def pulse(self, pulse_settings: PulseSettings):
        """Pulse driver."""
        pass

    def timed_enable(self, pulse_settings: PulseSettings, hold_settings: HoldSettings):
        """Pulse and enable the coil for an explicit duration."""
        raise NotImplementedError

    def enable(self, pulse_settings: PulseSettings, hold_settings: HoldSettings):
        """Enable driver."""
        pass

    def disable(self):
        """Disable driver."""
        pass

    def get_board_name(self):
        """Return board name."""
        return "TINYPINBALL"


class TinyPinballHardwarePlatform(
    SwitchPlatform,
    # LightsPlatform,
    DriverPlatform,
    # SegmentDisplaySoftwareFlashPlatform,
    # HardwareSoundPlatform,
    LogMixin,
):
    """TINYPINBALL platform."""

    __slots__ = ["config", "_poll_task", "_watchdog_task", "_inputs", "_coils_start_at_one", "_bus_lock",
                 "controller"]  # type: List[str]

    def __init__(self, machine) -> None:
        """Initialize platform."""
        super().__init__(machine)
        self._poll_task = None
        self._watchdog_task = None
        self._bus_lock = asyncio.Lock()
        self._inputs = {}               # type: Dict[str, bool]
        self._coils_start_at_one = None     # type: Optional[str]
        self.features['max_pulse'] = 255
        self.controller = None

        self.config = self.machine.config_validator.validate_config("tiny_pinball", self.machine.config['tiny_pinball'])
        self._configure_device_logging_and_debug("tinypinball", self.config)

    async def initialize(self):
        """Initialize platform."""

        # self.machine.clock._create_event_loop()

        async with self._bus_lock:

            await super().initialize()

            # #### Create Device Config ##### #
            config_yaml = ""

            # autofire_coils -> bumper: #kicker
            for coil_name in self.machine.config['autofire_coils']:
                coil = self.machine.config['autofire_coils'][coil_name]
                config_yaml += f"""
{coil_name}: #kicker
  trigger:
    port: {self.machine.config['switches'][coil["switch"]]["number"]}
  coil:
    port: {self.machine.config['coils'][coil["coil"]]["number"]}
  lamp:
    port: -1
  power: {coil["power"]}
  delay: {coil["delay"]}
  hold_time: {coil["hold_time"]}
  cooldown: {coil["cooldown"]}
"""

            print(config_yaml)

            self.controller = SoftwareController(self.config['port'])
            self.controller.connect()
            while True:
                try:
                    print(
                        self.controller.query(
                            ("name", "xyz"), "devices.pinguin.trigger.state"
                        )
                    )
                    break
                except UnknownDestination:
                    pass
                await asyncio.sleep(.1)

            print(
                self.controller.query(
                    ("name", "xyz"), "devices.pinguin.trigger.state"
                )
            )

            # self.debug_log("Reading all switches.")
            for switch in self.machine.config["switches"]:
                number = self.machine.config["switches"][switch]["number"]
                print(number)

                state = self.controller.query(
                    ("name", "xyz"), f"devices.{number}.trigger.state"
                )

                self._inputs[number] = state == 1

                print("pinguin")

    async def start(self):
        """Start reading switch changes."""
        self._poll_task = asyncio.create_task(self._poll())
        self._poll_task.add_done_callback(Util.raise_exceptions)

    def stop(self):
        """Stop platform."""
        super().stop()
        if self.controller:
            self.controller.disconnect()

        # wait for connections to close
        self.machine.clock.loop.run_until_complete(asyncio.sleep(.1))

    async def _poll(self):
        while True:
            async with self._bus_lock:
                for switch_num in self._inputs:

                    try:
                        raw_switch_state: str = (self.controller.query(
                            ("name", "xyz"), f"devices.{switch_num}.trigger.state"
                        ))

                        if '0>$setaddress' in raw_switch_state:
                            continue

                        switch_state: bool = bool(int(raw_switch_state))

                        if self._inputs[str(switch_num)] != switch_state:
                            # tell the switch controller about the new state
                            self.machine.switch_controller.process_switch_by_num(str(switch_num), switch_state, self)

                            # store in dict as well
                            self._inputs[switch_num] = switch_state
                    except Exception as e:
                        print(e)

    async def _watchdog(self):
        """Periodically send watchdog."""
        while True:
            # send watchdog
            async with self._bus_lock:
                pass
            # sleep 500ms
            await asyncio.sleep(.5)

    def set_pulse_on_hit_and_enable_and_release_rule(self, enable_switch: SwitchSettings, coil: DriverSettings):
        pass

    def set_pulse_on_hit_and_release_and_disable_rule(self, enable_switch: SwitchSettings,
                                                      eos_switch: SwitchSettings, coil: DriverSettings,
                                                      repulse_settings: Optional[RepulseSettings]):
        pass

    def set_pulse_on_hit_and_enable_and_release_and_disable_rule(self, enable_switch: SwitchSettings,
                                                                 eos_switch: SwitchSettings, coil: DriverSettings,
                                                                 repulse_settings: Optional[RepulseSettings]):
        pass

    def set_pulse_on_hit_and_release_rule(self, enable_switch: SwitchSettings, coil: DriverSettings):
        pass

    def set_pulse_on_hit_rule(self, enable_switch: SwitchSettings, coil: DriverSettings):
        pass

    def clear_hw_rule(self, switch: SwitchSettings, coil: DriverSettings):
        pass

    def configure_switch(self, number: str, config: SwitchConfig, platform_config: dict) -> SwitchPlatformInterface:
        """Configure a switch."""
        if number not in self._inputs:
            raise AssertionError("Invalid switch number {}. Platform reports the following switches as "
                                 "valid: {}".format(number, list(self._inputs.keys())))

        return TinyPinballSwitch(config=config, number=number, platform=self)

    async def get_hw_switch_states(self):
        """Return current switch states."""
        return self._inputs

    def configure_driver(self, config: DriverConfig, number: str, platform_settings: dict) -> DriverPlatformInterface:
        """Configure a driver."""

        driver = TinyPinballDriver(config=config, number=number)
        return driver

    def get_info_string(self):
        """Dump info about Tiny Pinball platform."""
        info: str = "TINYPINBALL connected via serial on {} \n".format(self.config['port'])
        info += "Input map: {}\n".format(sorted(list(self._inputs.keys())))
        return info
