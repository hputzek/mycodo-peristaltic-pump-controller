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
from mycodo.utils.lockfile import LockFile

measurements_dict = {
    key: {
        'measurement': 'output_ml',
        'unit': 'ml'
    }
    for key in range(6)
}
# Add alive status measurement
measurements_dict[6] = {
    'measurement': 'boolean',
    'unit': 'bool'
}

channels_dict = {
    key: {
        'types': ['volume'],
        'name': f'Pump {key + 1}',
        'measurements': [key]
    }
    for key in range(6)
}
# Add alive status channel
channels_dict[6] = {
    'types': ['on_off'],
    'name': 'Alive Status',
    'measurements': [6]
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
                ('5', '5'),
                ('6', '6'),
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
            'name': 'Amount (ml)',
            'phrase': 'How much to dispense (ml)'
        },
        {
            'id': 'input_button_dispense',
            'type': 'button',
            'name': '💧Dispense'
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
        },
        {
            'type': 'new_line'
        },
        {
            'id': 'input_button_ping',
            'type': 'button',
            'name': 'Ping (stirrer output will activate for 5 sec. if success)'
        },
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

    def initialize(self):
        """Code executed when Mycodo starts up to initialize the output."""

        # Set custom channel options to defaults or user-set values
        output_channels = db_retrieve_table_daemon(
            OutputChannel).filter(OutputChannel.output_id == self.output.unique_id).all()
        self.options_channels = self.setup_custom_channel_options_json(
            OUTPUT_INFORMATION['custom_channel_options'], output_channels)

        # Variables set by the user interface
        self.setup_output_variables(OUTPUT_INFORMATION)
        self.interface = self.output.interface
        if not self.output.uart_location:
            return

        self.device = PeristalticPumpController(self.output.uart_location)

        self.logger.info(self.output)

        self.logger.info("Output set up")
        if self.device.setup:
            self.logger.info(
                f"Output class initialized")

            # Check initial alive status
            if hasattr(self.device, 'check_alive_status'):
                alive_status = self.device.check_alive_status()
                for i in range(6):
                    self.output_states[i] = False
                self.output_states[6] = alive_status
                self.logger.info(f"Device online: {alive_status}")
                self.output_setup = True



    def record_dispersal(self, pump_number=None, amount_ml=None):
        measure_dict = copy.deepcopy(measurements_dict)
        if amount_ml and pump_number:
            measure_dict[pump_number - 1]['value'] = amount_ml

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
        # Check if this is the alive status channel
        if output_channel == 6:
            if state == 'on':
                self.output_states[output_channel] = True
                return True
            elif state == 'off':
                self.output_states[output_channel] = False
                return False
            return True

        # For regular pump channels
        if state == 'on' and output_type == 'vol' and amount > 0:
            self.logger.info("Output turned on")
            response = self.device.dispense(output_channel + 1, amount)
            self.logger.info(response)

            # Check alive status
            alive_status = self.device.check_alive_status()
            self.output_states[6] = alive_status  # Update the alive status in output_states

            self.record_dispersal(output_channel + 1, amount)
            self.output_states[output_channel] = True
            return True
        elif state == 'off':
            self.logger.info("Output turned off")
            self.output_states[output_channel] = False
            return False
        return True

    def is_on(self, output_channel=None):
        """Code to return the state of the output."""
        if self.is_setup():
            if output_channel is not None and output_channel in self.output_states:
                return self.output_states[output_channel]
            else:
                return self.output_states
        return False

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

    def input_button_dispense(self, args_dict):
        if not self.is_setup():
            self.logger.info("The output is not set up.")
            return True
        if not self.checkParams(args_dict):
            self.logger.error("Error: Invalid input parameters")
            return False
        # Check alive status
        alive_status = self.device.check_alive_status()
        self.output_states[6] = alive_status  # Update the alive status in output_states
        self.logger.info(self.device.dispense(args_dict['pump_number'], args_dict['dispense_ml']))
        self.record_dispersal(args_dict['pump_number'], args_dict['dispense_ml'])
        return True

    def input_button_start_calibration(self, args_dict):
        if not self.checkParams(args_dict):
            self.logger.error(
                "Error: Invalid input parameters"
            )
            return
        self.device.set_calibration_mode(args_dict['pump_number'], args_dict['dispense_ml'])

    def input_button_stop_calibration(self, args_dict):
        if not self.checkParams(args_dict):
            self.logger.error(
                "Error: Invalid input parameters"
            )
            return
        self.device.stop_calibration_mode()

    def input_button_ping(self, args_dict):
        if not self.checkParams(args_dict):
            self.logger.error(
                "Error: Invalid input parameters"
            )
            return
        ping_result = self.device.ping()
        if not ping_result:
            self.logger.error("Error: Device ping returned empty string")
            return {"error": "Device ping failure"}

        return {"success": "Device ping successful"}


class PeristalticPumpController:
    """
    Peristaltic Pump Controller
    """
    # Class variable to hold the shared serial connections
    connections = {}

    def __init__(self, serial_device_location):
        self.logger = logging.getLogger(
            "{}_{}".format(__name__, serial_device_location.replace("/", "_")))
        self.logger.info(serial_device_location)
        self.interface = 'UART'
        self.name = serial_device_location.replace("/", "_")
        self.lock_timeout = 5
        self.lock_file = '/var/lock/UART_{}_{}.lock'.format(
            __name__.replace(".", "_"), serial_device_location.replace("/", "_"))
        self.setup = False
        self.serial_device = serial_device_location

        if serial_device_location not in PeristalticPumpController.connections:
            try:
                PeristalticPumpController.connections[serial_device_location] = serial.Serial(
                    port=serial_device_location,
                    baudrate=9600,
                    timeout=self.lock_timeout,
                )
                self.logger.info("Serial connection established")
            except Exception as e:
                self.logger.error("Failed to initialize serial connection: {}".format(e))
        else:
            self.logger.info("Reusing existing serial connection")

        self.serial = PeristalticPumpController.connections[serial_device_location]

        try:
            cmd_return = self.ping()
            time.sleep(0.1)
            if cmd_return and isinstance(cmd_return, str):
                # Try to decode the JSON string and extract 'device' and 'version'
                try:
                    parsed_json = json.loads(cmd_return)
                    self.device = parsed_json['device']
                    self.version = parsed_json['version']
                    self.logger.info(
                        "Device: {device}, Version: {version}".format(
                            device=self.device,
                            version=self.version))
                    self.setup = True
                except (json.JSONDecodeError, KeyError) as e:
                    raise ValueError("Error parsing JSON: {}".format(e))

        except serial.SerialException as err:
            self.logger.exception(
                "{cls} raised an exception when initializing. Probably the wrong Port was selected.".format(
                    cls=type(self).__name__))

    def send_command(self, command, timeout=0.2):
        """
        Send a command through the serial connection.
        :param command: The command string to be sent.
        :param timeout: Time in seconds to wait for a response.
        :return: The complete response as a single string, or an error message if the operation fails.
        :raises IOError: If there is an issue with sending the command or reading the response.
        """

        lf = LockFile()
        if lf.lock_acquire(self.lock_file, self.lock_timeout):
            response = []
            try:
                self.serial.write(f"{command}\n".encode('utf-8'))
                time.sleep(0.05)
                end_time = time.time() + timeout
                while time.time() < end_time:
                    if self.serial.in_waiting > 0:  # Check if there is data in the buffer
                        try:
                            line = self.serial.readline().decode('utf-8')
                            response.append(line)
                        except SerialTimeoutException:
                            break
                        except Exception as e:
                            raise IOError(f"Error reading response: {e}")
            except SerialTimeoutException:
                raise IOError("Timeout while sending command.")
            except Exception as err:
                self.logger.exception(
                    "{cls} raised an exception when taking a reading: "
                    "{err}".format(cls=type(self).__name__, err=err))
                return "error", err
            finally:
                lf.lock_release(self.lock_file)
                return ''.join(response)
        return ""

    def dispense(self, pump_number, amount):
        """
        Dispense a specified amount of liquid using a designated stepper motor.
        Also checks the device's online status and updates the alive status.

        :param pump_number: ID of the stepper motor (1 to 6)
        :param amount: Amount of liquid in milliliters (float)
        :return: Response from the device
        """

        # Send the dispense command with command number based on stepper_number
        if int(pump_number) < 5:
            command = f"1 {pump_number} {amount}"
        else:
            hardware_pump_number = int(pump_number) - 4
            command = f"5 {hardware_pump_number} {amount}"
        response = self.send_command(command)

        return response


    def set_calibration_mode(self, pump_number, amount_ml=None):
        """
        Start calibration mode for a stepper motor.

        :param pump_number: ID of the stepper / motor (1 to 6)
        :param amount_ml: Amount of liquid in milliliters for calibration. Defaults to 300 ml if not specified.
        :return: Response from the device
        """
        if amount_ml is None:
            amount_ml = 300  # Default value

        if pump_number < 5:
            command = f"2 {pump_number} {amount_ml}"
        else:
            command = f"6 {pump_number} {amount_ml}"

        return self.send_command(command)

    def stop_calibration_mode(self):
        """
        Stop calibration mode for a stepper motor.

        :return: Response from the device
        """
        self.send_command(7)
        time.sleep(0.2)
        self.send_command(8)
        return True

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

    def check_alive_status(self):
        """
        Check if the device is online by sending command '9' and expecting a specific response.

        :return: True if the device is online, False otherwise
        """

        command = "9"
        self.serial.reset_input_buffer()
        response = self.send_command(command)

        try:
            # Try to parse the response as JSON
            parsed_response = json.loads(response)
            # Check if the response contains the expected values
            if (parsed_response.get('device') == 'PumpsX4' and
                    parsed_response.get('version') == '1.0'):
                return True
            else:
                self.logger.error("Unexpected response from device: {}".format(response))
            return False
        except (json.JSONDecodeError, TypeError, AttributeError):
            self.logger.error("Error parsing JSON response: {}".format(response))
            # If the response is not valid JSON or is None/empty
            return False
