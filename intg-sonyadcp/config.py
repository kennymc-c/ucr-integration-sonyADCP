"""This module contains some fixed variables, the media player entity definition class and the Setup class which includes all fixed and customizable variables"""

from enum import Enum
import json
import os
import logging
import hashlib
import base64
import uuid
import socket

import ucapi

import adcp as ADCP

_LOG = logging.getLogger(__name__)



class Sources (str, Enum):
    """Defines all sources for the media player entity"""
    HDMI_1 = "HDMI 1"
    HDMI_2 = "HDMI 2"

class SimpleCommands (str, Enum):
    """Defines all simple commands for the media player and remote entity"""
    INPUT_HDMI1 = "INPUT_HDMI_1"
    INPUT_HDMI2 = "INPUT_HDMI_2"
    PICTURE_MUTING_TOGGLE = "PICTURE_MUTING_TOGGLE"
    MODE_PRESET_REF = "MODE_PRESET_REF"
    MODE_PRESET_USER = "MODE_PRESET_USER"
    MODE_PRESET_TV = "MODE_PRESET_TV"
    MODE_PRESET_PHOTO = "MODE_PRESET_PHOTO"
    MODE_PRESET_GAME = "MODE_PRESET_GAME"
    MODE_PRESET_BRIGHT_CINEMA = "MODE_PRESET_BRIGHT_CINEMA"
    MODE_PRESET_BRIGHT_TV = "MODE_PRESET_BRIGHT_TV"
    MODE_PRESET_CINEMA_FILM_1 = "MODE_PRESET_CINEMA_FILM_1"
    MODE_PRESET_CINEMA_FILM_2 = "MODE_PRESET_CINEMA_FILM_2"
    MODE_ASPECT_RATIO_NORMAL = "MODE_ASPECT_RATIO_NORMAL"
    MODE_ASPECT_RATIO_ZOOM_1_85 = "MODE_ASPECT_RATIO_ZOOM_1_85"
    MODE_ASPECT_RATIO_ZOOM_2_35 = "MODE_ASPECT_RATIO_ZOOM_2_35"
    MODE_ASPECT_RATIO_V_STRETCH = "MODE_ASPECT_RATIO_V_STRETCH"
    MODE_ASPECT_RATIO_SQUEEZE = "MODE_ASPECT_RATIO_SQUEEZE"
    MODE_ASPECT_RATIO_STRETCH = "MODE_ASPECT_RATIO_STRETCH"
    MODE_MOTIONFLOW_OFF = "MODE_MOTIONFLOW_OFF"
    MODE_MOTIONFLOW_SMOOTH_HIGH = "MODE_MOTIONFLOW_SMOOTH_HIGH"
    MODE_MOTIONFLOW_SMOOTH_LOW = "MODE_MOTIONFLOW_SMOOTH_LOW"
    MODE_MOTIONFLOW_IMPULSE = "MODE_MOTIONFLOW_IMPULSE"
    MODE_MOTIONFLOW_COMBINATION = "MODE_MOTIONFLOW_COMBINATION"
    MODE_MOTIONFLOW_TRUE_CINEMA = "MODE_MOTIONFLOW_TRUE_CINEMA"
    MODE_HDR_ON = "MODE_HDR_ON"
    MODE_HDR_OFF = "MODE_HDR_OFF"
    MODE_HDR_AUTO = "MODE_HDR_AUTO"
    MODE_HDR_DYN_TONE_MAPPING_1 = "MODE_HDR_DYN_TONE_MAPPING_1"
    MODE_HDR_DYN_TONE_MAPPING_2 = "MODE_HDR_DYN_TONE_MAPPING_2"
    MODE_HDR_DYN_TONE_MAPPING_3 = "MODE_HDR_DYN_TONE_MAPPING_2"
    MODE_HDR_DYN_TONE_MAPPING_OFF = "MODE_HDR_DYN_TONE_MAPPING_OFF"
    MODE_2D_3D_SELECT_AUTO = "MODE_2D_3D_SELECT_AUTO"
    MODE_2D_3D_SELECT_3D = "MODE_2D_3D_SELECT_3D"
    MODE_2D_3D_SELECT_2D = "MODE_2D_3D_SELECT_2D"
    MODE_3D_FORMAT_SIMULATED_3D = "MODE_3D_FORMAT_SIMULATED_3D"
    MODE_3D_FORMAT_SIDE_BY_SIDE = "MODE_3D_FORMAT_SIDE_BY_SIDE"
    MODE_3D_FORMAT_OVER_UNDER = "MODE_3D_FORMAT_OVER_UNDER"
    MODE_DYN_IRIS_CONTROL_OFF = "MODE_DYN_IRIS_CONTROL_IRIS_OFF"
    MODE_DYN_IRIS_CONTROL_FULL = "MODE_DYN_IRIS_CONTROL_FULL"
    MODE_DYN_IRIS_CONTROL_LIMITED = "MODE_DYN_IRIS_CONTROL_LIMITED"
    MODE_DYN_LIGHT_CONTROL_OFF = "MODE_DYN_LIGHT_CONTROL_OFF"
    MODE_DYN_LIGHT_CONTROL_FULL = "MODE_DYN_LIGHT_CONTROL_FULL"
    MODE_DYN_LIGHT_CONTROL_LIMITED = "MODE_DYN_LIGHT_CONTROL_LIMITED"
    LASER_DIM_UP = "LASER_DIM_UP"
    LASER_DIM_DOWN = "LASER_DIM_DOWN"
    LAMP_CONTROL_LOW = "LAMP_CONTROL_LOW"
    LAMP_CONTROL_HIGH = "LAMP_CONTROL_HIGH"
    INPUT_LAG_REDUCTION_ON = "INPUT_LAG_REDUCTION_ON"
    INPUT_LAG_REDUCTION_OFF = "INPUT_LAG_REDUCTION_OFF"
    MENU_POSITION_BOTTOM_LEFT = "MENU_POSITION_BOTTOM_LEFT"
    MENU_POSITION_CENTER = "MENU_POSITION_CENTER"
    LENS_SHIFT_UP = "LENS_SHIFT_UP"
    LENS_SHIFT_DOWN = "LENS_SHIFT_DOWN"
    LENS_SHIFT_LEFT = "LENS_SHIFT_LEFT"
    LENS_SHIFT_RIGHT = "LENS_SHIFT_RIGHT"
    LENS_FOCUS_FAR = "LENS_FOCUS_FAR"
    LENS_FOCUS_NEAR = "LENS_FOCUS_NEAR"
    LENS_ZOOM_LARGE = "LENS_ZOOM_LARGE"
    LENS_ZOOM_SMALL = "LENS_ZOOM_SMALL"
    MODE_PICTURE_POSITION_1_85 = "PICTURE_POSITION_1_85"
    MODE_PICTURE_POSITION_2_35 = "PICTURE_POSITION_2_35"
    MODE_PICTURE_POSITION_CUSTOM_1 = "PICTURE_POSITION_CUSTOM_1"
    MODE_PICTURE_POSITION_CUSTOM_2 = "PICTURE_POSITION_CUSTOM_2"
    MODE_PICTURE_POSITION_CUSTOM_3 = "PICTURE_POSITION_CUSTOM_3"
    MODE_PICTURE_POSITION_CUSTOM_4 = "PICTURE_POSITION_CUSTOM_4"
    MODE_PICTURE_POSITION_CUSTOM_5 = "PICTURE_POSITION_CUSTOM_5"



#TODO Use dataclasses for mapping and entity definitions classes

# Replaces the need for match/case statements in the command handler
# Needed as you can't (re) map ucapi commands directly to ADCP commands
class UC2ADCP:
    """Maps entity commands to ADCP commands"""

    __cmd_map = {
        ucapi.media_player.Commands.ON: ADCP.Commands.POWER_ON,
        ucapi.media_player.Commands.OFF: ADCP.Commands.POWER_OFF,
        ucapi.media_player.Commands.TOGGLE: ADCP.Commands.POWER_TOGGLE,
        ucapi.media_player.Commands.HOME: ADCP.Commands.MENU,
        ucapi.media_player.Commands.MENU: ADCP.Commands.MENU,
        ucapi.media_player.Commands.BACK: ADCP.Commands.LEFT,
        ucapi.media_player.Commands.CURSOR_UP: ADCP.Commands.UP,
        ucapi.media_player.Commands.CURSOR_DOWN: ADCP.Commands.DOWN,
        ucapi.media_player.Commands.CURSOR_LEFT: ADCP.Commands.LEFT,
        ucapi.media_player.Commands.CURSOR_RIGHT: ADCP.Commands.RIGHT,
        ucapi.media_player.Commands.CURSOR_ENTER: ADCP.Commands.ENTER,
        SimpleCommands.LENS_SHIFT_UP: ADCP.Commands.LENS_SHIFT_UP,
        SimpleCommands.LENS_SHIFT_DOWN: ADCP.Commands.LENS_SHIFT_DOWN,
        SimpleCommands.LENS_SHIFT_LEFT: ADCP.Commands.LENS_SHIFT_LEFT,
        SimpleCommands.LENS_SHIFT_RIGHT: ADCP.Commands.LENS_SHIFT_RIGHT,
        SimpleCommands.LENS_FOCUS_FAR: ADCP.Commands.LENS_FOCUS_FAR,
        SimpleCommands.LENS_FOCUS_NEAR: ADCP.Commands.LENS_FOCUS_NEAR,
        SimpleCommands.LENS_ZOOM_LARGE: ADCP.Commands.LENS_ZOOM_LARGE,
        SimpleCommands.LENS_ZOOM_SMALL: ADCP.Commands.LENS_ZOOM_SMALL,
        SimpleCommands.LASER_DIM_UP: ADCP.Commands.LASER_DIM_UP,
        SimpleCommands.LASER_DIM_DOWN: ADCP.Commands.LASER_DIM_DOWN,
        #Add .value for commands that require a value to use the string an not the enum in f string
        ucapi.media_player.Commands.MUTE: f"{ADCP.Commands.MUTE.value} {ADCP.Values.States.ON.value}",
        ucapi.media_player.Commands.UNMUTE: f"{ADCP.Commands.MUTE.value} {ADCP.Values.States.OFF.value}",
        SimpleCommands.INPUT_HDMI1: f"{ADCP.Commands.INPUT.value} {ADCP.Values.Inputs.HDMI1.value}",
        SimpleCommands.INPUT_HDMI2: f"{ADCP.Commands.INPUT.value} {ADCP.Values.Inputs.HDMI2.value}",
        SimpleCommands.MODE_PRESET_BRIGHT_CINEMA: f"{ADCP.Commands.PICTURE_MODE.value} {ADCP.Values.PictureModes.BRIGHT_CINEMA.value}",
        SimpleCommands.MODE_PRESET_BRIGHT_TV: f"{ADCP.Commands.PICTURE_MODE.value} {ADCP.Values.PictureModes.BRIGHT_TV.value}",
        SimpleCommands.MODE_PRESET_CINEMA_FILM_1: f"{ADCP.Commands.PICTURE_MODE.value} {ADCP.Values.PictureModes.CINEMA_FILM1.value}",
        SimpleCommands.MODE_PRESET_CINEMA_FILM_2: f"{ADCP.Commands.PICTURE_MODE.value} {ADCP.Values.PictureModes.CINEMA_FILM2.value}",
        SimpleCommands.MODE_PRESET_REF: f"{ADCP.Commands.PICTURE_MODE.value} {ADCP.Values.PictureModes.REFERENCE.value}",
        SimpleCommands.MODE_PRESET_TV: f"{ADCP.Commands.PICTURE_MODE.value} {ADCP.Values.PictureModes.TV.value}",
        SimpleCommands.MODE_PRESET_PHOTO: f"{ADCP.Commands.PICTURE_MODE.value} {ADCP.Values.PictureModes.PHOTO.value}",
        SimpleCommands.MODE_PRESET_GAME: f"{ADCP.Commands.PICTURE_MODE.value} {ADCP.Values.PictureModes.GAME.value}",
        SimpleCommands.MODE_PRESET_USER: f"{ADCP.Commands.PICTURE_MODE.value} {ADCP.Values.PictureModes.USER.value}",
        SimpleCommands.MODE_ASPECT_RATIO_NORMAL: f"{ADCP.Commands.ASPECT.value} {ADCP.Values.Aspect.NORMAL.value}",
        SimpleCommands.MODE_ASPECT_RATIO_V_STRETCH: f"{ADCP.Commands.ASPECT.value} {ADCP.Values.Aspect.V_STRETCH.value}",
        SimpleCommands.MODE_ASPECT_RATIO_ZOOM_1_85: f"{ADCP.Commands.ASPECT.value} {ADCP.Values.Aspect.ZOOM_1_85.value}",
        SimpleCommands.MODE_ASPECT_RATIO_ZOOM_2_35: f"{ADCP.Commands.ASPECT.value} {ADCP.Values.Aspect.ZOOM_2_35.value}",
        SimpleCommands.MODE_ASPECT_RATIO_STRETCH: f"{ADCP.Commands.ASPECT.value} {ADCP.Values.Aspect.STRETCH.value}",
        SimpleCommands.MODE_ASPECT_RATIO_SQUEEZE: f"{ADCP.Commands.ASPECT.value} {ADCP.Values.Aspect.SQUEEZE.value}",
        SimpleCommands.MODE_PICTURE_POSITION_1_85: f"{ADCP.Commands.PICTURE_POSITION.value} {ADCP.Values.PicturePositions.PP_1_85.value}",
        SimpleCommands.MODE_PICTURE_POSITION_2_35: f"{ADCP.Commands.PICTURE_POSITION.value} {ADCP.Values.PicturePositions.PP_2_35.value}",
        SimpleCommands.MODE_PICTURE_POSITION_CUSTOM_1: f"{ADCP.Commands.PICTURE_POSITION.value} {ADCP.Values.PicturePositions.CUSTOM1.value}",
        SimpleCommands.MODE_PICTURE_POSITION_CUSTOM_2: f"{ADCP.Commands.PICTURE_POSITION.value} {ADCP.Values.PicturePositions.CUSTOM2.value}",
        SimpleCommands.MODE_PICTURE_POSITION_CUSTOM_3: f"{ADCP.Commands.PICTURE_POSITION.value} {ADCP.Values.PicturePositions.CUSTOM3.value}",
        SimpleCommands.MODE_PICTURE_POSITION_CUSTOM_4: f"{ADCP.Commands.PICTURE_POSITION.value} {ADCP.Values.PicturePositions.CUSTOM4.value}",
        SimpleCommands.MODE_PICTURE_POSITION_CUSTOM_5: f"{ADCP.Commands.PICTURE_POSITION.value} {ADCP.Values.PicturePositions.CUSTOM5.value}",
        SimpleCommands.MODE_MOTIONFLOW_OFF: f"{ADCP.Commands.MOTIONFLOW.value} {ADCP.Values.Motionflow.OFF.value}",
        SimpleCommands.MODE_MOTIONFLOW_COMBINATION: f"{ADCP.Commands.MOTIONFLOW.value} {ADCP.Values.Motionflow.COMBINATION.value}",
        SimpleCommands.MODE_MOTIONFLOW_SMOOTH_HIGH: f"{ADCP.Commands.MOTIONFLOW.value} {ADCP.Values.Motionflow.SMOOTH_HIGH.value}",
        SimpleCommands.MODE_MOTIONFLOW_SMOOTH_LOW: f"{ADCP.Commands.MOTIONFLOW.value} {ADCP.Values.Motionflow.SMOOTH_LOW.value}",
        SimpleCommands.MODE_MOTIONFLOW_IMPULSE: f"{ADCP.Commands.MOTIONFLOW.value} {ADCP.Values.Motionflow.IMPULSE.value}",
        SimpleCommands.MODE_MOTIONFLOW_TRUE_CINEMA: f"{ADCP.Commands.MOTIONFLOW.value} {ADCP.Values.Motionflow.TRUE_CINEMA.value}",
        SimpleCommands.MODE_HDR_ON: f"{ADCP.Commands.HDR.value} {ADCP.Values.HDR.ON.value}",
        SimpleCommands.MODE_HDR_OFF: f"{ADCP.Commands.HDR.value} {ADCP.Values.HDR.OFF.value}",
        SimpleCommands.MODE_HDR_AUTO: f"{ADCP.Commands.HDR.value} {ADCP.Values.HDR.AUTO.value}",
        SimpleCommands.MODE_HDR_DYN_TONE_MAPPING_1: f"{ADCP.Commands.HDR_DYN_TONE_MAPPING.value} {ADCP.Values.HDRDynToneMapping.MODE_1.value}",
        SimpleCommands.MODE_HDR_DYN_TONE_MAPPING_2: f"{ADCP.Commands.HDR_DYN_TONE_MAPPING.value} {ADCP.Values.HDRDynToneMapping.MODE_2.value}",
        SimpleCommands.MODE_HDR_DYN_TONE_MAPPING_3: f"{ADCP.Commands.HDR_DYN_TONE_MAPPING.value} {ADCP.Values.HDRDynToneMapping.MODE_3.value}",
        SimpleCommands.MODE_HDR_DYN_TONE_MAPPING_OFF: f"{ADCP.Commands.HDR_DYN_TONE_MAPPING.value} {ADCP.Values.HDRDynToneMapping.OFF.value}",
        SimpleCommands.MODE_2D_3D_SELECT_AUTO: f"{ADCP.Commands.MODE_2D_3D.value} {ADCP.Values.Mode2D3D.MODE_AUTO.value}",
        SimpleCommands.MODE_2D_3D_SELECT_3D: f"{ADCP.Commands.MODE_2D_3D.value} {ADCP.Values.Mode2D3D.MODE_3D.value}",
        SimpleCommands.MODE_2D_3D_SELECT_2D: f"{ADCP.Commands.MODE_2D_3D.value} {ADCP.Values.Mode2D3D.MODE_2D.value}",
        SimpleCommands.MODE_3D_FORMAT_SIMULATED_3D: f"{ADCP.Commands.MODE_3D_FORMAT.value} {ADCP.Values.Mode3DFormat.SIMULATED.value}",
        SimpleCommands.MODE_3D_FORMAT_SIDE_BY_SIDE: f"{ADCP.Commands.MODE_3D_FORMAT.value} {ADCP.Values.Mode3DFormat.SIDE_BY_SIDE.value}",
        SimpleCommands.MODE_3D_FORMAT_OVER_UNDER: f"{ADCP.Commands.MODE_3D_FORMAT.value} {ADCP.Values.Mode3DFormat.OVER_UNDER.value}",
        SimpleCommands.MODE_DYN_IRIS_CONTROL_OFF: f"{ADCP.Commands.DYN_IRIS_CONTROL.value} {ADCP.Values.LightControl.OFF.value}",
        SimpleCommands.MODE_DYN_IRIS_CONTROL_FULL: f"{ADCP.Commands.DYN_IRIS_CONTROL.value} {ADCP.Values.LightControl.FULL.value}",
        SimpleCommands.MODE_DYN_IRIS_CONTROL_LIMITED: f"{ADCP.Commands.DYN_IRIS_CONTROL.value} {ADCP.Values.LightControl.LIMITED.value}",
        SimpleCommands.MODE_DYN_LIGHT_CONTROL_OFF: f"{ADCP.Commands.DYN_LIGHT_CONTROL.value} {ADCP.Values.LightControl.OFF.value}",
        SimpleCommands.MODE_DYN_LIGHT_CONTROL_FULL: f"{ADCP.Commands.DYN_LIGHT_CONTROL.value} {ADCP.Values.LightControl.FULL.value}",
        SimpleCommands.MODE_DYN_LIGHT_CONTROL_LIMITED: f"{ADCP.Commands.DYN_LIGHT_CONTROL.value} {ADCP.Values.LightControl.LIMITED.value}",
        SimpleCommands.LAMP_CONTROL_LOW: f"{ADCP.Commands.LAMP_CONTROL.value} {ADCP.Values.LampControl.LOW.value}",
        SimpleCommands.LAMP_CONTROL_HIGH: f"{ADCP.Commands.LAMP_CONTROL.value} {ADCP.Values.LampControl.HIGH.value}",
        SimpleCommands.INPUT_LAG_REDUCTION_ON: f"{ADCP.Commands.INPUT_LAG.value} {ADCP.Values.States.ON.value}",
        SimpleCommands.INPUT_LAG_REDUCTION_OFF: f"{ADCP.Commands.INPUT_LAG.value} {ADCP.Values.States.OFF.value}",
        SimpleCommands.MENU_POSITION_BOTTOM_LEFT: f"{ADCP.Commands.MENU_POSITION.value} {ADCP.Values.MenuPosition.BOTTOM_LEFT.value}",
        SimpleCommands.MENU_POSITION_CENTER: f"{ADCP.Commands.MENU_POSITION.value} {ADCP.Values.MenuPosition.CENTER.value}",
    }

    @staticmethod
    def get(key):
        """Get the string value from the specified enum key in __cmd_map"""
        try:
            if UC2ADCP.__cmd_map[key] == "":
                raise ValueError(f"Got empty value for key {key}")
            return UC2ADCP.__cmd_map[key]
        except KeyError as k:
            raise KeyError(f"Couldn't find a matching ADCP command for command {key}") from k



class MpDef:
    """Media player entity definition class that includes the device class, features, attributes and options"""
    device_class = ucapi.media_player.DeviceClasses.TV
    features = [
        ucapi.media_player.Features.ON_OFF,
        ucapi.media_player.Features.TOGGLE,
        ucapi.media_player.Features.MUTE,
        ucapi.media_player.Features.UNMUTE,
        ucapi.media_player.Features.MUTE_TOGGLE,
        ucapi.media_player.Features.DPAD,
        ucapi.media_player.Features.HOME,
        ucapi.media_player.Features.SELECT_SOURCE
        ]
    attributes = {
        ucapi.media_player.Attributes.STATE: ucapi.media_player.States.UNKNOWN,
        ucapi.media_player.Attributes.MUTED: False,
        ucapi.media_player.Attributes.SOURCE: "",
        ucapi.media_player.Attributes.SOURCE_LIST: [cmd.value for cmd in Sources]
        }
    options = {
        ucapi.media_player.Options.SIMPLE_COMMANDS: [cmd.value for cmd in SimpleCommands]
        }



class RemoteDef:
    """Remote entity definition class that includes the features, attributes and simple commands"""
    features = [
        ucapi.remote.Features.ON_OFF,
        ucapi.remote.Features.TOGGLE,
        ]
    attributes = {
        ucapi.remote.Attributes.STATE: ucapi.remote.States.UNKNOWN
        }
    simple_commands = [cmd.value for cmd in SimpleCommands]



class LTSensorDef:
    """Light source timer sensor entity definition class that includes the device class, attributes and options"""
    device_class = ucapi.sensor.DeviceClasses.CUSTOM
    attributes = {
        ucapi.sensor.Attributes.STATE: ucapi.sensor.States.ON,
        ucapi.sensor.Attributes.UNIT: "h"
        }
    options = {
        ucapi.sensor.Options.CUSTOM_UNIT: "h"
        }



class PasswordManager:
    """Class to encrypt and decrypt the ADCP password."""

    @staticmethod
    def generate_salt() -> str:
        """Generate a unique salt from the hostname."""
        try:
            # Using the hostname to generate the salt seems to be the best compromise for an architecture independent method that works on all platforms, \
            # doesn't has to be stored somewhere and always returns the same value unless the hostname changes which the average user usually won't do. \
            # Getting the remotes serial using the additional WS core api is too complicated and also needs an api key or the pin code form the user
            #TODO Add to Readme that when changing the hostname or using a configuration file from a different system the integration has to be reconfigured
            unique_identifier = str(uuid.uuid5(uuid.NAMESPACE_DNS, socket.gethostname()))
            _LOG.debug(f"Generated unique identifier for salt: {unique_identifier}")
        except Exception as e:
            _LOG.error(f"Failed to generate user identifier: {e}")
            raise

        return hashlib.sha256(unique_identifier.encode()).hexdigest()

    @staticmethod
    def _generate_key(salt: str) -> bytes:
        """Generate a 32-byte key using SHA-256."""
        return hashlib.sha256(salt.encode()).digest()

    @staticmethod
    def encrypt_password(password: str, salt: str) -> str:
        """Encrypt the password using XOR and Base64."""
        key = PasswordManager._generate_key(salt)
        encrypted = bytes([p ^ key[i % len(key)] for i, p in enumerate(password.encode())])
        return base64.b64encode(encrypted).decode()

    @staticmethod
    def decrypt_password(encrypted_password: str, salt: str) -> str:
        """Decrypt the password using XOR and Base64."""
        key = PasswordManager._generate_key(salt)
        encrypted = base64.b64decode(encrypted_password)
        decrypted = bytes([e ^ key[i % len(key)] for i, e in enumerate(encrypted)])
        return decrypted.decode()



class Setup:
    """Setup class which includes all fixed and customizable variables including functions to set() and get() them from a runtime storage
    which includes storing them in a json config file and as well as load() them from this file"""

    __conf = {
        "ip": "",
        "id": "",
        "name": "",
        "rt-id": "",
        "lt-id": "",
        "lt-name": "",
        "setup_complete": False,
        "setup_reconfigure": False,
        "setup_step": "init",
        "standby": False,
        "bundle_mode": False,
        "mp_poller_interval": 20,  # Use 0 to deactivate; will be automatically set to 0 when running on the remote (bundle_mode: True)
        "lt_poller_interval": 1800,  # Use 0 to deactivate
        "adcp_port": 53595,
        "adcp_password": "",
        "adcp_timeout": 5,
        "sdap_port": 53862,
        "cfg_path": "config.json"
    }
    __setters = ["ip", "id", "name", "rt-id", "lt-id", "lt-name", "setup_complete", "setup_reconfigure", "setup_step", "standby", "bundle_mode",
                 "mp_poller_interval", "lt_poller_interval", "cfg_path", "adcp_port", "adcp_password", "adcp_timeout", "sdap_port"]
    __storers = ["setup_complete", "ip", "id", "name", "adcp_port", "adcp_password", "adcp_timeout", "sdap_port",
                 "mp_poller_interval", "lt_poller_interval"]  # Skip runtime only related keys in config file

    @staticmethod
    def get(key):
        """Get the value from the specified key in __conf"""
        if Setup.__conf[key] == "" and key != "adcp_password": #Password can be empty if ADCP authentication is not enabled
            raise ValueError("Got empty value for key " + key + " from runtime storage")

        return Setup.__conf[key]

    @staticmethod
    def set_lt_name_id(mp_entity_id: str, mp_entity_name: str):
        """Generate light source timer sensor entity id and name and store it"""
        _LOG.info("Generate light source timer sensor entity id and name")
        lt_entity_id = "lighttimer-"+mp_entity_id
        lt_entity_name = {
            "en": "Light source Timer "+mp_entity_name,
            "de": "Lichtquellen-Timer "+mp_entity_name
        }
        try:
            Setup.set("lt-id", lt_entity_id)
            Setup.set("lt-name", lt_entity_name)
        except ValueError as v:
            raise ValueError(v) from v

    @staticmethod
    def set(key, value, store: bool = True):
        """Set and store a value for the specified key into the runtime storage and config file."""

        if key in Setup.__setters:
            if Setup.__conf["setup_reconfigure"] and key == "setup_complete":
                _LOG.debug("Ignore setting and storing setup_complete flag during reconfiguration")

            else:
                Setup.__conf[key] = value
                if key == "adcp_password":
                    _LOG.debug(f"Stored {key} into runtime storage")
                else:
                    _LOG.debug(f"Stored {key}: {value} into runtime storage")

                if not store:
                    _LOG.debug("Store set to False. Value will not be stored in config file this time")

                else:
                    if key == "adcp_password":
                        salt = PasswordManager.generate_salt()
                        value = PasswordManager.encrypt_password(value, salt)
                        _LOG.debug(f"Encrypt ADCP password before storing to {Setup.__conf['cfg_path']}")

                    if key in Setup.__storers:
                        jsondata = {key: value}
                        if os.path.isfile(Setup.__conf["cfg_path"]):

                            try:
                                with open(Setup.__conf["cfg_path"], "r+", encoding="utf-8") as f:
                                    l = json.load(f)
                                    l.update(jsondata)
                                    f.seek(0)
                                    f.truncate()  # Needed when the new value has less characters than the old value (e.g. false to true)
                                    json.dump(l, f)

                                    if key == "adcp_password":
                                        _LOG.debug(f"Stored {key} into {Setup.__conf['cfg_path']}")
                                    else:
                                        _LOG.debug(f"Stored {key}: {value} into {Setup.__conf['cfg_path']}")

                            except OSError as o:
                                raise OSError(o) from o
                            except Exception as e:
                                if key == "adcp_password":
                                    raise Exception(f"Error while storing {key} into {Setup.__conf['cfg_path']}") from e
                                raise Exception(f"Error while storing {key}: {value} into {Setup.__conf['cfg_path']}") from e

                        # Create config file first if it doesn't exist yet
                        else:
                            # Skip storing setup_complete if no config files exist
                            if key != "setup_complete":

                                try:
                                    with open(Setup.__conf["cfg_path"], "w", encoding="utf-8") as f:
                                        json.dump(jsondata, f)

                                    if key == "adcp_password":
                                        _LOG.debug(f"Stored {key} into {Setup.__conf['cfg_path']}")
                                    else:
                                        _LOG.debug(f"Stored {key}: {value} into {Setup.__conf['cfg_path']}")

                                except OSError as o:
                                    raise OSError(o) from o

                                except Exception as e:
                                    if key == "adcp_password":
                                        raise Exception(f"Error while storing {key} into {Setup.__conf['cfg_path']}") from e
                                    raise Exception(f"Error while storing {key}: {value} into {Setup.__conf['cfg_path']}") from e

                    else:
                        _LOG.debug(f"{key} will not be stored in the config file")
        else:
            raise NameError(f"{key} should not be changed")

    @staticmethod
    def load():
        """Load all variables from the config json file into the runtime storage"""

        if os.path.isfile(Setup.__conf["cfg_path"]):
            try:
                with open(Setup.__conf["cfg_path"], "r", encoding="utf-8") as f:
                    configfile = json.load(f)

            except Exception as e:
                raise OSError(f"Error while reading {Setup.__conf['cfg_path']}") from e

            if configfile == "":
                raise OSError(f"Error in {Setup.__conf['cfg_path']}. No data")

            Setup.__conf["setup_complete"] = configfile["setup_complete"]
            _LOG.debug(f"Loaded setup_complete: {configfile['setup_complete']} into runtime storage from {Setup.__conf['cfg_path']}")

            if not Setup.__conf["setup_complete"]:
                _LOG.warning("The setup was not completed the last time. Please restart the setup process")

            else:
                if "adcp_password" in configfile:
                    try:
                        salt = PasswordManager.generate_salt()
                        Setup.__conf["adcp_password"] = PasswordManager.decrypt_password(configfile["adcp_password"], salt)
                        _LOG.debug("Decrypted ADCP password after loading")
                    except Exception as e:
                        _LOG.info("Failed to decrypt the ADCP password. Has the hostname changed? If yes, please reconfigure the integration")
                        raise Exception(e) from e

                if "ip" in configfile:
                    Setup.__conf["ip"] = configfile["ip"]
                    _LOG.debug("Loaded ip into runtime storage from " + Setup.__conf["cfg_path"])
                else:
                    _LOG.debug("Skip loading ip as it's not yet stored in the config file")

                if "id" and "name" in configfile:
                    Setup.__conf["id"] = configfile["id"]
                    Setup.__conf["name"] = configfile["name"]
                    _LOG.debug("Loaded id and name into runtime storage from " + Setup.__conf["cfg_path"])
                else:
                    _LOG.debug("Skip loading id and name as there are not yet stored in the config file")

                if "adcp_port" in configfile:
                    Setup.__conf["adcp_port"] = configfile["adcp_port"]
                    _LOG.debug("Loaded ADCP port " + str(configfile["adcp_port"]) + " into runtime storage from " + Setup.__conf["cfg_path"])

                if "adcp_timeout" in configfile:
                    Setup.__conf["adcp_timeout"] = configfile["adcp_port"]
                    _LOG.debug("Loaded ADCP timeout " + str(configfile["adcp_timeout"]) + " into runtime storage from " + Setup.__conf["cfg_path"])

                if "sdap_port" in configfile:
                    Setup.__conf["sdap_port"] = configfile["sdap_port"]
                    _LOG.debug("Loaded SDAP port " + str(configfile["sdap_port"]) + " into runtime storage from " + Setup.__conf["cfg_path"])

                if "mp_poller_interval" in configfile:
                    Setup.__conf["mp_poller_interval"] = configfile["mp_poller_interval"]
                    _LOG.debug("Loaded power/mute/input poller interval of " + str(configfile["mp_poller_interval"]) + " seconds into runtime storage \
                               from " + Setup.__conf["cfg_path"])

                if "lt_poller_interval" in configfile:
                    Setup.__conf["lt_poller_interval"] = configfile["lt_poller_interval"]
                    _LOG.debug("Loaded light source timer poller interval of " + str(configfile["lt_poller_interval"]) + " seconds into runtime storage \
                               from " + Setup.__conf["cfg_path"])

        else:
            _LOG.info(Setup.__conf["cfg_path"] + " does not exist (yet). Please start the setup process")
