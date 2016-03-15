"""Contains the drivers and interface code for pinball machines which
use the Multimorphic R-ROC hardware controllers.

This code can be used with P-ROC driver boards, or with Stern SAM, Stern
Whitestar, Williams WPC, or Williams WPC95 driver boards.

Much of this code is from the P-ROC drivers section of the pyprocgame project,
written by Adam Preble and Gerry Stellenberg. It was originally released under
the MIT license and is released here under the MIT License.

More info on the P-ROC hardware platform: http://pinballcontrollers.com/

Original code source on which this module was based:
https://github.com/preble/pyprocgame

"""

import logging
from mpf.platforms.p_roc_common import PDBConfig, PROCDriver, PROCMatrixLight, PROCBasePlatform
from mpf.core.utility_functions import Util

try:
    import pinproc
except ImportError:
    pinproc = None


class HardwarePlatform(PROCBasePlatform):
    """Platform class for the P-ROC hardware controller.

    Args:
        machine: The MachineController instance.

    Attributes:
        machine: The MachineController instance.
    """

    def __init__(self, machine):
        super(HardwarePlatform, self).__init__(machine)
        self.log = logging.getLogger('P-ROC')
        self.log.debug("Configuring P-ROC hardware")

        # validate config for p_roc
        self.machine.config_validator.validate_config("p_roc", self.machine.config['p_roc'])

        # ----------------------------------------------------------------------
        # Platform-specific hardware features. WARNING: Do not edit these. They
        # are based on what the P-ROC hardware can and cannot do.
        self.features['max_pulse'] = 255
        self.features['hw_rule_coil_delay'] = False
        self.features['variable_recycle_time'] = False
        self.features['variable_debounce_time'] = False
        self.features['hw_led_fade'] = True
        # todo need to add differences between patter and pulsed_patter

        # Make the platform features available to everyone
        self.machine.config['platform'] = self.features
        # ----------------------------------------------------------------------

        self.connect()

        # Clear out the default program for the aux port since we might need it
        # for a 9th column. Details:
        # http://www.pinballcontrollers.com/forum/index.php?topic=1360
        commands = []
        commands += [self.pinproc.aux_command_disable()]

        for dummy_iterator in range(1, 255):
            commands += [self.pinproc.aux_command_jump(0)]

        self.proc.aux_send_commands(0, commands)
        # End of the clear out the default program for the aux port.

        # Because PDBs can be configured in many different ways, we need to
        # traverse the YAML settings to see how many PDBs are being used.
        # Then we can configure the P-ROC appropriately to use those PDBs.
        # Only then can we relate the YAML coil/light #'s to P-ROC numbers for
        # the collections.
        if self.machine_type == self.pinproc.MachineTypePDB:
            self.log.debug("Configuring P-ROC for PDBs (P-ROC driver boards)")
            self.pdbconfig = PDBConfig(self.proc, self.machine.config, self.pinproc.DriverCount)

        else:
            self.log.debug("Configuring P-ROC for OEM driver boards")

    def __repr__(self):
        return '<Platform.P-ROC>'

    def stop(self):
        self.proc.reset(1)

    def configure_driver(self, config, device_type='coil'):
        """Creates a P-ROC driver.

        Typically drivers are coils or flashers, but for the P-ROC this is
        also used for matrix-based lights.

        Args:
            config: Dictionary of settings for the driver.
            device_type: String with value of either 'coil' or 'switch'.

        Returns:
            A reference to the PROCDriver object which is the actual object you
            can use to pulse(), patter(), enable(), etc.

        """
        # todo need to add Aux Bus support
        # todo need to add virtual driver support for driver counts > 256

        # Find the P-ROC number for each driver. For P-ROC driver boards, the
        # P-ROC number is specified via the Ax-By-C format. For OEM driver
        # boards configured via driver numbers, libpinproc's decode() method
        # can provide the number.

        if self.machine_type == self.pinproc.MachineTypePDB:
            proc_num = self.pdbconfig.get_proc_number(device_type,
                                                      str(config['number']))
            if proc_num == -1:
                self.log.error("Coil cannot be controlled by the P-ROC. "
                               "Ignoring.")
                return
        else:
            proc_num = self.pinproc.decode(self.machine_type, str(config['number']))

        if device_type in ['coil', 'flasher']:
            proc_driver_object = PROCDriver(proc_num, self.proc, config, self.machine)
        elif device_type == 'light':
            proc_driver_object = PROCMatrixLight(proc_num, self.proc)
        else:
            raise AssertionError("Invalid device type {}".format(device_type))

        if 'polarity' in config:
            state = proc_driver_object.proc.driver_get_state(config['number'])
            state['polarity'] = config['polarity']
            proc_driver_object.proc.driver_update_state(state)

        return proc_driver_object, config['number']

    def configure_switch(self, config):
        """Configures a P-ROC switch.

        Args:
            config: Dictionary of settings for the switch. In the case
                of the P-ROC, it uses the following:

        Returns:
            switch : A reference to the switch object that was just created.
            proc_num : Integer of the actual hardware switch number the P-ROC
                uses to refer to this switch. Typically your machine
                configuration files would specify a switch number like `SD12` or
                `7/5`. This `proc_num` is an int between 0 and 255.

        """
        proc_num = self.pinproc.decode(self.machine_type, str(config['number']))
        return self._configure_switch(config, proc_num)

    def get_hw_switch_states(self):
        # Read in and set the initial switch state
        # The P-ROC uses the following values for hw switch states:
        # 1 - closed (debounced)
        # 2 - open (debounced)
        # 3 - closed (not debounced)
        # 4 - open (not debounced)

        states = self.proc.switch_get_states()

        for switch, state in enumerate(states):
            if state == 3 or state == 1:
                states[switch] = 1
            else:
                states[switch] = 0

        return states

    def configure_dmd(self):
        """Configures a hardware DMD connected to a classic P-ROC."""
        return PROCDMD(self.proc, self.machine)

    def tick(self, dt):
        """Checks the P-ROC for any events (switch state changes or notification
        that a DMD frame was updated).

        Also tickles the watchdog and flushes any queued commands to the P-ROC.

        """
        del dt
        # Get P-ROC events (switches & DMD frames displayed)
        for event in self.proc.get_events():
            event_type = event['type']
            event_value = event['value']
            if event_type == 99:  # CTRL-C to quit todo does this go here?
                self.machine.stop()
            elif event_type == self.pinproc.EventTypeDMDFrameDisplayed:
                pass
            elif event_type == self.pinproc.EventTypeSwitchClosedDebounced:
                self.machine.switch_controller.process_switch_by_num(state=1,
                                                                     num=event_value)
            elif event_type == self.pinproc.EventTypeSwitchOpenDebounced:
                self.machine.switch_controller.process_switch_by_num(state=0,
                                                                     num=event_value)
            elif event_type == self.pinproc.EventTypeSwitchClosedNondebounced:
                self.machine.switch_controller.process_switch_by_num(state=1,
                                                                     num=event_value,
                                                                     debounced=False)
            elif event_type == self.pinproc.EventTypeSwitchOpenNondebounced:
                self.machine.switch_controller.process_switch_by_num(state=0,
                                                                     num=event_value,
                                                                     debounced=False)
            else:
                self.log.warning("Received unrecognized event from the P-ROC. "
                                 "Type: %s, Value: %s", event_type, event_value)

        self.proc.watchdog_tickle()
        self.proc.flush()


class PROCDMD(object):
    """Parent class for a physical DMD attached to a P-ROC.

    Args:
        proc: Reference to the MachineController's proc attribute.
        machine: Reference to the MachineController

    Attributes:
        dmd: Reference to the P-ROC's DMD buffer.

    """

    def __init__(self, proc, machine):
        self.proc = proc
        self.machine = machine
        self.dmd = pinproc.DMDBuffer(128, 32)
        # size is hardcoded here since 128x32 is all the P-ROC hw supports

        # dmd_timing defaults should be 250, 400, 180, 800

        if self.machine.config['p_roc']['dmd_timing_cycles']:

            dmd_timing = Util.string_to_list(self.machine.config['p_roc']['dmd_timing_cycles'])

            self.proc.dmd_update_config(high_cycles=dmd_timing)

        # Schedule DMD updates
        self.machine.clock.schedule_interval(self.tick, self.machine.config['p_roc']['dmd_update_interval'] / 1000.0)

    def update(self, data):
        """Updates the DMD with a new frame.

        Args:
            data: A 4096-byte raw string.

        """
        if len(data) == 4096:
            self.dmd.set_data(data)
        else:
            self.machine.log.warning("Received a DMD frame of length %s instead"
                                     "of 4096. Discarding...", len(data))

    def tick(self, dt):
        """Updates the physical DMD with the latest frame data. Meant to be
        called once per machine tick.

        """
        del dt
        self.proc.dmd_draw(self.dmd)
