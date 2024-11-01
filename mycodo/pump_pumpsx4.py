# coding=utf-8
#
# example_dummy_output.py - Example Output module
#
import json
import logging
import time
import copy

import serial
from serial.serialutil import SerialTimeoutException

from mycodo.databases.models import OutputChannel
from mycodo.outputs.base_output import AbstractOutput
from mycodo.utils.database import db_retrieve_table_daemon
from mycodo.utils.constraints_pass import constraints_pass_positive_value
from mycodo.utils.influx import add_measurements_influxdb

measurements_dict = {
    key: {
        'measurement': 'output_ml',
        'unit': 'ml'
    }
    for key in range(4)
}

channels_dict = {
    key: {
        'types': ['volume'],
        'name': f'Pump {key + 1}',
        'measurements': [key]
    }
    for key in range(4)
}

# Output information
OUTPUT_INFORMATION = {
    # A unique output name used to distinguish it from others
    'output_name_unique': 'PumpsX4',

    # A friendly/common name for the output to display to the user
    'output_name': 'PumpsX4 Output',

    # The dictionaries of measurements and channels for this output
    'measurements_dict': measurements_dict,
    'channels_dict': channels_dict,

    # Type of output. Options: "on_off", "pwm", "volume"
    'output_types': ['volume'],

    # A message to display at the top of the output options
    'message': 'A four channel peristaltic pump controller based on the CNC shield 3.0. Find documentation in the link.',

    'url_manufacturer': 'https://github.com/hputzek/mycodo-peristaltic-pump-controller',

    # Form input options that are enabled or disabled
    'options_enabled': [
        'uart_location'
    ],
    'options_disabled': [
        # 'interface'  # Show the interface (as a disabled input)
    ],

    # Any dependencies required by the output module. An empty list means no dependencies are required.
    'dependencies_module': [],

    # A message to be displayed on the dependency install page
    'dependencies_message': 'Are you sure you want to install these dependencies? They require...',

    # The interface or interfaces that can be used with this module
    # A custom interface can be used.
    # Options: SHELL, PYTHON, GPIO, I2C, FTDI, UART, IP
    'interfaces': ['UART'],

    # Custom actions that will appear at the top of the options in the user interface.
    # Buttons are required to have a function with the same name that will be executed
    # when the button is pressed. Input values will be passed to the button in a
    # dictionary. See the function input_button() at the end of this module.
    'custom_commands_message': 'Immediately stop all pumps:',
    'custom_commands': [
        {
            'id': 'input_button_stop_pumps',
            'type': 'button',
            'name': 'Emergency stop'
        },
        {
            'type': 'new_line'
        },
        {
            'id': 'pump_number',
            'type': 'select',
            'default_value': '1',
            'options_select': [
                ('1', '1'),
                ('2', '2'),
                ('3', '3'),
                ('4', '4'),
            ],
            'name': 'Pump number',
            'phrase': 'Select which pump to control',
            'constraints_pass': constraints_pass_positive_value
        },
        {
            'id': 'dispense_ml',
            'type': 'float',
            'default_value': 10.0,
            'constraints_pass': constraints_pass_positive_value,
            'name': 'Dispense amount (ml)',
            'phrase': 'How much to dispense (ml)'
        },
        {
            'id': 'input_button_dispense_amount',
            'type': 'button',
            'name': 'Dispense amount'
        },
        {
            'id': 'input_button_start_calibration',
            'type': 'button',
            'name': 'Start calibration'
        },
        {
            'id': 'input_button_stop_calibration',
            'type': 'button',
            'name': 'Stop calibration'
        }
    ],

    # Custom options that can be set by the user in the web interface.
    'custom_options_message': 'No optional config available.',
    'custom_options': [

    ],

    # Options that appear for each Channel
    'custom_channel_options': [

    ]
}


class OutputModule(AbstractOutput):
    """An output support class that operates an output."""

    def __init__(self, output, testing=False):
        super().__init__(output, testing=testing, name=__name__)

        self.interface = None
        self.output_setup = False
        self.device: PeristalticPumpController | None = None
        # Set custom option variables to defaults or user-set values
        self.setup_custom_options(
            OUTPUT_INFORMATION['custom_options'], output)

        # Set custom channel options to defaults or user-set values
        output_channels = db_retrieve_table_daemon(
            OutputChannel).filter(OutputChannel.output_id == self.output.unique_id).all()
        self.options_channels = self.setup_custom_channel_options_json(
            OUTPUT_INFORMATION['custom_channel_options'], output_channels)

    def initialize(self):
        """Code executed when Mycodo starts up to initialize the output."""
        # Variables set by the user interface
        self.setup_output_variables(OUTPUT_INFORMATION)
        self.interface = self.output.interface
        if not self.output.uart_location:
            return

        self.device = PeristalticPumpController(self.output.uart_location)

        self.logger.info(self.output)

        self.logger.info(
            f"Output class initialized")
        self.logger.info(self.device.ping())

        # Variable to store whether the output has been successfully set up
        self.logger.info("Output set up")
        self.output_setup = True

    def record_dispersal(self, pump_number=None, amount_ml=None):
        measure_dict = copy.deepcopy(measurements_dict)
        if amount_ml and pump_number:
            measure_dict[pump_number-1]['value'] = amount_ml

        add_measurements_influxdb(self.unique_id, measure_dict)

    def output_switch(self, state, output_type=None, amount=None, duty_cycle=None, output_channel=None):
        if not self.is_setup():
            msg = "Error 101: Device not set up. See https://kizniche.github.io/Mycodo/Error-Codes#error-101 for more info."
            self.logger.error(msg)
            return msg

        self.logger.info(state, output_type, amount, duty_cycle, output_channel)
        self.logger.info(
            f"Output switch called with state={state}, output_type={output_type}, amount={amount}, duty_cycle={duty_cycle}, output_channel={output_channel}"
        )
        """
        Set the output on, off, to an amount, or to a duty cycle
        output_type can be None, 'sec', 'vol', or 'pwm', and determines the amount's unit
        """
        if state == 'on' and output_type == 'vol' and amount > 0:
            self.logger.info("Output turned on")
            self.output_states[output_channel] = True
            self.logger.info(self.device.dispense(output_channel + 1, amount))
            self.record_dispersal(output_channel + 1, amount)
            self.output_states[output_channel] = False
        elif state == 'off':
            self.logger.info("Output turned off")
            self.output_states[output_channel] = False

    def is_on(self, output_channel=None):
        """Code to return the state of the output."""
        if self.is_setup():
            if output_channel is not None and output_channel in self.output_states:
                return self.output_states[output_channel]
            else:
                return self.output_states

    def is_setup(self):
        """Returns whether the output has successfully been set up."""
        return self.output_setup

    def checkParams(self, args_dict):
        params_to_check = {'pump_number': str, 'dispense_ml': float}

        for param, expected_type in params_to_check.items():  # Use .items() here
            if param not in args_dict:
                self.logger.error(f"{param} is required but not provided")
                return False
            if not isinstance(args_dict[param], expected_type):
                self.logger.error(
                    f"Input value for {param} does not represent a {expected_type.__name__}: "
                    f"'{args_dict[param]}', type: {type(args_dict[param])}"
                )
                return False
        return True

    def input_button_stop_pumps(self, args_dict):
        """Executed when custom action button pressed."""
        self.logger.info(self.device.reset_all())
        self.logger.error("Stopped all pumps.")

    def input_button_dispense_amount(self, args_dict):
        if not self.checkParams(args_dict):
            self.logger.error(
                "Error: Invalid input parameters"
            )
            return
        self.logger.info(self.device.dispense(args_dict['pump_number'], args_dict['dispense_ml']))
        self.record_dispersal(args_dict['pump_number'], args_dict['dispense_ml'])

    def input_button_start_calibration(self, args_dict):
        if not self.checkParams(args_dict):
            self.logger.error(
                "Error: Invalid input parameters"
            )
            return
        self.device.set_calibration_mode(args_dict['pump_number'], 1,args_dict['dispense_ml'])

    def input_button_stop_calibration(self, args_dict):
        if not self.checkParams(args_dict):
            self.logger.error(
                "Error: Invalid input parameters"
            )
            return
        self.device.set_calibration_mode(args_dict['pump_number'], 0)
        

class PeristalticPumpController:
    """
     Peristaltic Pump Controller
    """

    def __init__(self, serial_device):
        self.logger = logging.getLogger(
            "{}_{}".format(__name__, serial_device.replace("/", "_")))
        self.logger.info(serial_device)
        self.interface = 'UART'
        self.name = serial_device.replace("/", "_")

        self.lock_timeout = 5
        self.lock_file = '/var/lock/PumpsX4_UART_{}_{}.lock'.format(
            __name__.replace(".", "_"), serial_device.replace("/", "_"))

        self.setup = False
        self.serial_device = serial_device

        try:
            self.pumpsX4 = serial.Serial(
                port=serial_device,
                baudrate=9600,
                timeout=5,
            )
            self.pumpsX4.write_timeout = 5

            cmd_return = self.ping()
            time.sleep(0.1)
            if cmd_return:
                # Try to decode the JSON string and extract 'device' and 'version'
                try:

                    self.logger.info("Raw JSON:")
                    self.logger.info(cmd_return)
                    parsed_json = json.loads(cmd_return)
                    self.device = parsed_json['device']
                    self.version = parsed_json['version']
                except (json.JSONDecodeError, KeyError) as e:
                    raise ValueError("Error parsing JSON: {}".format(e))

                self.logger.info(
                    "Device: {device}, Version: {version}".format(
                        device=self.device,
                        version=self.version))
                self.setup = True

        except serial.SerialException as err:
            self.logger.exception(
                "{cls} raised an exception when initializing: "
                "{err}".format(cls=type(self).__name__, err=err))
            self.logger.exception('Opening serial')

    def send_command(self, command, timeout=5.0):
        """
        Send a command through the serial connection.
        :param command: The command string to be sent.
        :param timeout: Time in seconds to wait for a response.
        :return: The complete response as a single string, or an error message if the operation fails.
        :raises IOError: If there is an issue with sending the command or reading the response.
        """
        try:
            self.pumpsX4.write(f"{command}\n".encode('utf-8'))
        except SerialTimeoutException:
            raise IOError("Timeout while sending command.")
        except Exception as e:
            raise IOError(f"Failed to send command: {e}")

        response = []
        end_time = time.time() + timeout
        time.sleep(0.1)  # Small sleep to prevent excessive CPU usage
        while time.time() < end_time:
            if self.pumpsX4.in_waiting > 0:  # Check if there is data in the buffer
                try:
                    char = self.pumpsX4.read()
                except SerialTimeoutException:
                    break
                if char:
                    response.append(char.decode('utf-8'))


        if not response:
            raise IOError("No response received within the timeout period.")

        return ''.join(response)

    def dispense(self, stepper_number, amount):
        """
        Dispense a specified amount of liquid using a designated stepper motor.

        :param stepper_number: ID of the stepper motor (1 to 4)
        :param amount: Amount of liquid in milliliters (float)
        :return: Response from the device
        """
        command = f"1 {stepper_number} {amount}"
        return self.send_command(command)

    def set_calibration_mode(self, stepper_number, status, amount_ml=None):
        """
        Set the calibration mode for a stepper motor.

        :param stepper_number: ID of the stepper motor (1 to 4)
        :param status: 1 to start calibration mode, 0 to stop
        :param amount_ml: Amount of liquid in milliliters for calibration. Defaults to 300 ml if not specified.
        :return: Response from the device
        """
        if amount_ml is None:
            amount_ml = 300  # Default value

        command = f"2 {stepper_number} {status} {amount_ml}" if status == 1 else f"2 {stepper_number} {status}"
        return self.send_command(command)

    def ping(self):
        """
        Ping the device to confirm the connection.

        :return: Response from the device
        """
        command = "3"
        return self.send_command(command)

    def reset_all(self):
        """
        Immediately stop all motors.

        :return: Response from the device
        """
        command = "4"
        return self.send_command(command)
