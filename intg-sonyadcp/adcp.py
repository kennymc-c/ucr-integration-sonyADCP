#!/usr/bin/env python3

"""This file is used to define selected commands as Enums and a send function for the Sony ADCP protocol"""

import logging
from enum import Enum

import socket
from struct import unpack
import hashlib
import asyncio


_LOG = logging.getLogger(__name__)


#These are just a fraction of available ADCP commands. For a full list of supported commands refer to the external links at README.md/#ADCP-supported-commands-list

class Get (str, Enum):
    """This class is used to define commands that return a value from the projector"""

    POWER = "power_status ?"
    INPUT = "input ?"
    MUTE = "blank ?"
    COLOR_SPACE = "color_space ?"
    MODE_2D_3D = "3d_status ?"
    #Response only:
    SIGNAL = "signal ?"
    TIMER = "timer ?"
    TEMPERATURE = "temperature ?"
    WARNING = "warning ?"
    ERROR = "error ?"
    MODEL = "modelname ?"
    SERIAL = "serialnum ?"
    MAC = "\"mac_address ? \""

class Commands (str, Enum):
    """This class is used to define commands that can be send the projector"""

    #Need additional values:
    POWER_ON = "power \"on\""
    POWER_OFF = "power \"off\""
    INPUT = "input"
    PICTURE_MODE = "picture_mode"
    PICTURE_POSITION = "pic_pos_sel"
    ASPECT = "aspect"
    MOTIONFLOW = "motionflow"
    HDR = "hdr"
    HDR_DYN_TONE_MAPPING = "hdr_tone_mapping"
    MODE_2D_3D = "2d3d_sel"
    MODE_3D_FORMAT = "3d_format"
    DYN_IRIS_CONTROL = "iris_dyn_cont"
    DYN_LIGHT_CONTROL = "light_output_dyn"
    LAMP_CONTROL = "lamp_control"
    INPUT_LAG = "input_lag_red"
    MENU_POSITION = "menu_pos"
    MUTE = "blank"
    #Keys that are working without values:
    POWER_TOGGLE = "key \"power\""
    MENU = "key \"menu\""
    UP = "key \"up\""
    DOWN = "key \"down\""
    LEFT = "key \"left\""
    RIGHT = "key \"right\""
    ENTER = "key \"enter\""
    LENS_FOCUS_NEAR = "key \"lens_focus_near\""
    LENS_FOCUS_FAR = "key \"lens_focus_far\""
    LENS_ZOOM_LARGE = "key \"lens_zoom_up\""
    LENS_ZOOM_SMALL = "key \"lens_zoom_down\""
    LENS_SHIFT_UP = "key \"lens_shift_up\""
    LENS_SHIFT_DOWN = "key \"lens_shift_down\""
    LENS_SHIFT_LEFT = "key \"lens_shift_left\""
    LENS_SHIFT_RIGHT = "key \"lens_shift_right\""
    LASER_DIM_UP = "key \"laser_brightness+\""
    LASER_DIM_DOWN = "key \"laser_brightness-\""

class Values():
    """Includes all classes with values that can be combined with commands"""

    class States (str, Enum):
        """This class is used to define states that can be used in conjunction with certain commands"""

        ON = "\"on\""
        OFF = "\"off\""
        STANDBY = "\"standby\""
        STARTUP = "\"startup\""
        COOLING1 = "\"cooling1\""
        COOLING2 = "\"cooling2\""

    class Inputs (str, Enum):
        """This class is used to define the input sources that can be used with the input command"""

        HDMI1 = "\"hdmi1\""
        HDMI2 = "\"hdmi2\""

    class PictureModes (str, Enum):
        """This class is used to define the picture modes that can be used with the picture_mode command"""

        CINEMA_FILM1 = "\"cinema_film1\""
        CINEMA_FILM2 = "\"cinema_film2\""
        REFERENCE = "\"reference\""
        TV = "\"tv\""
        PHOTO = "\"photo\""
        BRIGHT_CINEMA = "\"brt_cinema\""
        BRIGHT_TV = "\"brt_tv\""
        USER = "\"user\""
        USER1 = "\"user1\""
        USER2 = "\"user2\""
        USER3 = "\"user3\""
        GAME = "\"game\""

    class PicturePositions (str, Enum):
        """This class is used to define the picture positions that can be used with the picture_position command"""

        PP_1_85 = "\"1.85_1\""
        PP_2_35 = "\"2.35_1\""
        CUSTOM1 = "\"custom1\""
        CUSTOM2 = "\"custom2\""
        CUSTOM3 = "\"custom3\""
        CUSTOM4 = "\"custom4\""
        CUSTOM5 = "\"custom5\""

    class Aspect (str, Enum):
        """This class is used to define the aspect ratios that can be used with the aspect command"""

        FULL1 = "\"full1\""
        FULL2 = "\"full2\""
        NORMAL = "\"normal\""
        STRETCH = "\"stretch\""
        V_STRETCH = "\"v_stretch\""
        SQUEEZE = "\"squeeze\""
        ZOOM_1_85 = "\"1.85_1_zoom\""
        ZOOM_2_35 = "\"2.35_1_zoom\""

    class Motionflow(str, Enum):
        """This class is used to define the motionflow modes that can be used with the motionflow command"""

        SMOOTH_HIGH = "\"smooth_high\""
        SMOOTH_LOW = "\"smooth_low\""
        IMPULSE = "\"impulse\""
        COMBINATION = "\"combination\""
        TRUE_CINEMA = "\"true_cinema\""
        OFF = "\"off\""

    class HDR(str, Enum):
        """HDR settings available on the projector"""
        ON = "\"on\""
        OFF = "\"off\""
        AUTO = "\"auto\""
        HLG = "\"hlg\""
        HDR10 = "\"hdr10\""
        HDR_REF = "\"hdr_reference\""

    class HDRDynToneMapping(str, Enum):
        """HDR dynamic tone mapping settings available on the projector"""
        MODE_1 = "\"mode1\""
        MODE_2 = "\"mode2\""
        MODE_3 = "\"mode3\""
        OFF = "\"off\""

    class LampControl(str, Enum):
        """Lamp control settings available on the projector"""
        LOW = "\"low\""
        HIGH = "\"high\""

    class LightControl(str, Enum):
        """Iris / light source dynamic control settings available on the projector"""
        OFF = "\"off\""
        FULL = "\"full\""
        LIMITED = "\"limited\""

    class Mode2D3D(str, Enum):
        """2D/3D mode settings available on the projector"""
        MODE_AUTO = "\"auto\""
        MODE_3D = "\"3d\""
        MODE_2D = "\"2d\""

    class Mode3DFormat(str, Enum):
        """3D format settings available on the projector"""
        SIMULATED = "\"simulated\""
        SIDE_BY_SIDE = "\"sidebyside\""
        OVER_UNDER = "\"overunder\""

    class MenuPosition(str, Enum):
        """Menu position settings available on the projector"""
        BOTTOM_LEFT = "\"bottom_left\""
        CENTER = "\"center\""

    class ColorSpaces (str, Enum):
        """This class is used to define the color spaces that can be used with the color_space  command"""

        BT709 = "\"bt709\""
        BT2020 = "\"bt2020\""
        COLOR_SPACE1 = "\"color_space1\""
        COLOR_SPACE2 = "\"color_space2\""
        COLOR_SPACE3 = "\"color_space3\""
        CUSTOM = "\"custom\""

    class ColorTemps (str, Enum):
        """This class is used to define the color temps that can be used with the color_temp command"""
        CUSTOM1 = "\"custom1\""
        CUSTOM2 = "\"custom2\""
        CUSTOM3 = "\"custom3\""
        CUSTOM4 = "\"custom4\""
        CUSTOM5 = "\"custom5\""
        D93 = "\"d93\""
        D75 = "\"d75\""
        D65 = "\"d65\""
        D55 = "\"d55\""

class Responses():
    """Includes all classes with responses that can be returned by response only get commands"""

    class Errors (str, Enum):
        """This class is used to define errors that will be returned with the error ? get command. Multiple values can be returned in a json array"""
        NO = "\"no_err\""
        POWER = "\"err_power\"" #Main power supply error
        POWER2 = "\"err_power2\"" #DC power supply or NAND error
        SYSTEM3 = "\"err_system3\"" #MAIN_STARTUP
        SYSTEM4 = "\"err_system4\"" #WDT
        SYSTEM5 = "\"err_system5\"" #BE_STARTUP
        COVER = "\"err_cover\""
        LIGHT_SRC = "\"err_light_src\""
        LENS_COVER = "\"err_lens_cover\""
        SHOCK = "\"err_shock\""
        NOLENS = "\"err_nolens\""
        ANGLE = "\"err_attitude\""
        TEMP = "\"err_temp\""
        FAN = "\"err_fan\""
        WHEEL = "\"err_wheel\""
        LUMINANCE = "\"err_light_over\""
        ASSY = "\"err_assy\""
        BALLAST = "\"err_ballast_update\""

    class Warning (str, Enum):
        """This class is used to define warnings that will be returned with the warning ? get command. Multiple values can be returned in a json array"""
        NO = "\"no_warn\""
        LIGHT_SRC_LIFE = "\"warn_light_src_life\""
        ALTITUDE = "\"warn_highland\""
        TEMP = "\"warn_temp\""
        SIGNAL_FREQ = "\"warn_signal_freq\""
        SIGNAL_TYPE = "\"warn_signal_sel\""



class Projector:
    """This class is used to define the projector object and its methods"""
    def __init__(self, ip: str = None, sdap_port: int = 53862, adcp_port: int = 53595, adcp_timeout: int = 5, adcp_password: str = "Projector"):
        """
        :param ip: str, IP address for projector. Can be empty when using get_pjinfo
        :param sdap_port: int, SDAP Advertisement UDP port. If not given 53862 will be used
        :param adcp_port: int, ADCP TCP port. If not given 53595 will be used
        :param adcp_timeout: int, Timeout for ADCP TCP communication. If not given 5 seconds will be used
        :param adcp_password: str, Password for ADCP communication. If not given the factory default password will be used
        """

        # Default values
        self.ip = ip
        self.adcp_port = adcp_port
        self.adcp_password = adcp_password
        self.adcp_timeout = adcp_timeout
        self.sdap_port = sdap_port
        self.sdap_timeout = 31 #30 sec is the default SDAP advertisement interval

    async def get_pjinfo(self):
        """
        Returns ip, serial, and model name from the projector via SDAP advertisement service as a dictionary.

        Can take up to 30 seconds when using the default SDAP advertisement interval.
        """
        try:
            # Socket Setup
            sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            sock.bind(("", self.sdap_port))
            sock.settimeout(self.sdap_timeout)

            # Receive Data
            def receive_data():
                return sock.recvfrom(1028)  # Blocking call to receive data and address

            try:
                sdap_buffer, addr = await asyncio.to_thread(receive_data)
                if not sdap_buffer or len(sdap_buffer) < 24:
                    _LOG.error("Invalid or empty data received")
                    return None

                # Parse Data
                serial = unpack(">I", sdap_buffer[20:24])[0]
                model_bytes = sdap_buffer[8:20].strip(b"\x00")
                if not model_bytes:
                    _LOG.error("Empty model data")
                    return None

                model = model_bytes.decode("ascii", errors="ignore")
                ip = addr[0]

                if not all([serial, model, ip]):
                    _LOG.error(f"Invalid data: serial={serial}, model={model}, ip={ip}")
                    return None

                return {"model": model, "serial": serial, "ip": ip}

            except socket.timeout as t:
                _LOG.error("SDAP timeout waiting for projector advertisement")
                raise TimeoutError("No projector response within timeout") from t

            except (UnicodeDecodeError, IndexError) as e:
                _LOG.error(f"Failed to parse projector data: {e}")
                return None

        except Exception as e:
            _LOG.error(f"SDAP communication error: {str(e)}")
            return None
        finally:
            try:
                sock.close()
            except Exception:
                pass

    async def command(self, command):
        """Send an ADCP command to the projector and return the response using async socket connection"""

        if isinstance(command, Enum):
            command = command.value

        try:
            async with asyncio.timeout(self.adcp_timeout):
                reader, writer = await asyncio.open_connection(self.ip, self.adcp_port)

                initial_hash = (await reader.readline()).decode("ASCII").strip()
                authenticated = False

                if "NOKEY" in initial_hash:
                    authenticated = True
                    _LOG.debug("Received NOKEY. No ADCP authentication needed.")
                else:
                    hash_pw = initial_hash + self.adcp_password
                    encrypt_hash = hashlib.sha256(hash_pw.encode()).hexdigest()
                    writer.write(f"{encrypt_hash}\r\n".encode("ASCII"))
                    await writer.drain()

                    auth_reply = (await reader.readline()).decode("ASCII").strip()

                    if "OK" in auth_reply:
                        authenticated = True
                    elif "err_auth" in auth_reply:
                        raise PermissionError("ADCP authentication error. Please check the configured ADCP password")
                    else:
                        raise PermissionError(f"Unexpected ADCP authentication response: {auth_reply}")

                if authenticated:
                    writer.write(f"{command}\r\n".encode("ASCII"))
                    await writer.drain()

                    _LOG.debug(f"Sent ADCP command: {command}")

                    response = (await reader.readline()).decode("ASCII").strip()

                    writer.close()
                    await writer.wait_closed()

                    if response:
                        if "err_cmd" in response:
                            raise NameError(f"ADCP command \"{command}\" can not be recognized or is not supported on this model")
                        elif "err_val" in response:
                            raise ValueError(f"Value error in ADCP command \"{command}\". Value is out of range or invalid")
                        elif "err_option" in response:
                            raise AttributeError(f"Option in ADCP command \"{command}\" not supported, invalid or missing")
                        elif "err_inactive" in response:
                            raise Exception(f"ADCP command \"{command}\" temporarily unavailable")
                        elif "err_internal1" in response or "err_internal2" in response:
                            raise Exception(f"Internal ADCP communication error while sending command \"{command}\"")
                        elif (response.startswith('"') or response.startswith("[")) and (response.endswith('"') or response.endswith("]")):
                            _LOG.debug(f"Received ADCP query value response: {response}")
                            return response
                        elif command.endswith("?"):
                            _LOG.debug(f"Received ADCP query numeric value response: {response}")
                            return response
                        elif response == "ok":
                            return True
                        else:
                            raise Exception(f"Received an unknown ADCP response for command \"{command}\": {response}")
                    else:
                        raise Exception(f"Received no ADCP response for command \"{command}\"")

        except asyncio.TimeoutError as timeout:
            _LOG.error(f"ADCP timeout occurred after {self.adcp_timeout} seconds while sending command \"{command}\"")
            raise TimeoutError from timeout
        except ConnectionRefusedError as con_refused:
            _LOG.error(f"ADCP connection to projector refused while sending command \"{command}\". \
Please check if port {self.adcp_port} is the correct port and if the projector is reachable from the network")
            raise ConnectionRefusedError from con_refused
        except ConnectionResetError as con_reset:
            _LOG.error(f"ADCP connection to projector was reset for command \"{command}\". \
Please check if port {self.adcp_port} is the correct port and if the projector is reachable from the network")
            raise ConnectionResetError from con_reset
        except ConnectionError as con_error:
            _LOG.error(f"ADCP connection error while sending command \"{command}\"")
            raise ConnectionError from con_error
        except PermissionError as perm_error:
            _LOG.error(f"Authentication error while sending ADCP command \"{command}\": {perm_error}")
            raise PermissionError from perm_error
        except (Exception, NameError, ValueError, AttributeError) as error:
            _LOG.error(f"Failed to send ADCP command: {error}")
            raise Exception from error
