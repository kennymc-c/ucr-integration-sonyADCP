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

import media_player
import remote
import adcp as ADCP

_LOG = logging.getLogger(__name__)



class Sources (str, Enum):
    """Defines all sources for the media player entity"""
    HDMI_1 = "HDMI 1"
    HDMI_2 = "HDMI 2"

class SimpleCommands (str, Enum):
    """Defines all simple commands for the media player and remote entity.
    Maximum 20 upper case only characters including -/_.:+#*°@%()? allowed"""

    INPUT_HDMI1 =                                               "INPUT_HDMI_1"
    INPUT_HDMI2 =                                               "INPUT_HDMI_2"
    MODE_PRESET_REF =                                           "MODE_PIC_REF"
    MODE_PRESET_USER =                                          "MODE_PIC_USER"
    MODE_PRESET_TV =                                            "MODE_PIC_TV"
    MODE_PRESET_PHOTO =                                         "MODE_PIC_PHOTO"
    MODE_PRESET_GAME =                                          "MODE_PIC_GAME"
    MODE_PRESET_BRIGHT_CINEMA =                                 "MODE_PIC_BRT_CINEMA"
    MODE_PRESET_BRIGHT_TV =                                     "MODE_PIC_BRT_TV"
    MODE_PRESET_CINEMA_FILM_1 =                                 "MODE_PIC_CINE_FILM_1"
    MODE_PRESET_CINEMA_FILM_2 =                                 "MODE_PIC_CINE_FILM_2"
    MODE_ASPECT_RATIO_NORMAL =                                  "MODE_AR_NORMAL"
    MODE_ASPECT_RATIO_ZOOM_1_85 =                               "MODE_AR_ZOOM_1.85"
    MODE_ASPECT_RATIO_ZOOM_2_35 =                               "MODE_AR_ZOOM_2.35"
    MODE_ASPECT_RATIO_V_STRETCH =                               "MODE_AR_V_STRETCH"
    MODE_ASPECT_RATIO_SQUEEZE =                                 "MODE_AR_SQUEEZE"
    MODE_ASPECT_RATIO_STRETCH =                                 "MODE_AR_STRETCH"
    MODE_MOTIONFLOW_OFF =                                       "MODE_MOTION_OFF"
    MODE_MOTIONFLOW_SMOOTH_HIGH =                               "MODE_MOTION_SMTH_HIGH"
    MODE_MOTIONFLOW_SMOOTH_LOW =                                "MODE_MOTION_SMTH_LOW"
    MODE_MOTIONFLOW_IMPULSE =                                   "MODE_MOTION_IMPULSE"
    MODE_MOTIONFLOW_COMBINATION =                               "MODE_MOTION_COMB"
    MODE_MOTIONFLOW_TRUE_CINEMA =                               "MODE_MOTION_TRUE_CIN"
    MODE_HDR_ON =                                               "MODE_HDR_ON"
    MODE_HDR_OFF =                                              "MODE_HDR_OFF"
    MODE_HDR_AUTO =                                             "MODE_HDR_AUTO"
    MODE_HDR_DYN_TONE_MAPPING_1 =                               "MODE_HDR_TONEMAP_1"
    MODE_HDR_DYN_TONE_MAPPING_2 =                               "MODE_HDR_TONEMAP_2"
    MODE_HDR_DYN_TONE_MAPPING_3 =                               "MODE_HDR_TONEMAP_3"
    MODE_HDR_DYN_TONE_MAPPING_OFF =                             "MODE_HDR_TONEMAP_OFF"
    MODE_2D_3D_SELECT_AUTO =                                    "MODE_2D/3D_SEL_AUTO"
    MODE_2D_3D_SELECT_3D =                                      "MODE_2D/3D_SEL_3D"
    MODE_2D_3D_SELECT_2D =                                      "MODE_2D/3D_SEL_2D"
    MODE_3D_FORMAT_SIMULATED_3D =                               "MODE_3D_SIM_3D"
    MODE_3D_FORMAT_SIDE_BY_SIDE =                               "MODE_3D_SIDE_BY_SIDE"
    MODE_3D_FORMAT_OVER_UNDER =                                 "MODE_3D_OVER_UNDER"
    MODE_DYN_IRIS_CONTROL_OFF =                                 "MODE_DYN_IRIS_OFF"
    MODE_DYN_IRIS_CONTROL_FULL =                                "MODE_DYN_IRIS_FULL"
    MODE_DYN_IRIS_CONTROL_LIMITED =                             "MODE_DYN_IRIS_LIM"
    MODE_DYN_LIGHT_CONTROL_OFF =                                "MODE_DYN_LIGHT_OFF"
    MODE_DYN_LIGHT_CONTROL_FULL =                               "MODE_DYN_LIGHT_FULL"
    MODE_DYN_LIGHT_CONTROL_LIMITED =                            "MODE_DYN_LIGHT_LIM"
    INPUT_LAG_REDUCTION_ON =                                    "MODE_LAG_REDUCE_ON"
    INPUT_LAG_REDUCTION_OFF =                                   "MODE_LAG_REDUCE_OFF"
    LENS_SHIFT_UP =                                             "LENS_SHIFT_UP"
    LENS_SHIFT_DOWN =                                           "LENS_SHIFT_DOWN"
    LENS_SHIFT_LEFT =                                           "LENS_SHIFT_LEFT"
    LENS_SHIFT_RIGHT =                                          "LENS_SHIFT_RIGHT"
    LENS_FOCUS_FAR =                                            "LENS_FOCUS_FAR"
    LENS_FOCUS_NEAR =                                           "LENS_FOCUS_NEAR"
    LENS_ZOOM_LARGE =                                           "LENS_ZOOM_LARGE"
    LENS_ZOOM_SMALL =                                           "LENS_ZOOM_SMALL"
    PICTURE_POSITION_SELECT_1_85 =                              "PIC_POS_SEL_1:85"
    PICTURE_POSITION_SELECT_2_35 =                              "PIC_POS_SEL_2:35"
    PICTURE_POSITION_SELECT_CUSTOM_1 =                          "PIC_POS_SEL_CUSTOM_1"
    PICTURE_POSITION_SELECT_CUSTOM_2 =                          "PIC_POS_SEL_CUSTOM_2"
    PICTURE_POSITION_SELECT_CUSTOM_3 =                          "PIC_POS_SEL_CUSTOM_3"
    PICTURE_POSITION_SELECT_CUSTOM_4 =                          "PIC_POS_SEL_CUSTOM_4"
    PICTURE_POSITION_SELECT_CUSTOM_5 =                          "PIC_POS_SEL_CUSTOM_5"
    PICTURE_POSITION_SAVE_1_85 =                                "PIC_POS_SAV_1:85"
    PICTURE_POSITION_SAVE_2_35 =                                "PIC_POS_SAV_2:35"
    PICTURE_POSITION_SAVE_CUSTOM_1 =                            "PIC_POS_SAV_CUSTOM_1"
    PICTURE_POSITION_SAVE_CUSTOM_2 =                            "PIC_POS_SAV_CUSTOM_2"
    PICTURE_POSITION_SAVE_CUSTOM_3 =                            "PIC_POS_SAV_CUSTOM_3"
    PICTURE_POSITION_SAVE_CUSTOM_4 =                            "PIC_POS_SAV_CUSTOM_4"
    PICTURE_POSITION_SAVE_CUSTOM_5 =                            "PIC_POS_SAV_CUSTOM_5"
    PICTURE_MUTING_TOGGLE =                                     "MUTING_PIC_TOGGLE"
    LASER_DIM_UP =                                              "LASER_DIM_UP"
    LASER_DIM_DOWN =                                            "LASER_DIM_DOWN"
    LAMP_CONTROL_LOW =                                          "LAMP_CONTROL_LOW"
    LAMP_CONTROL_HIGH =                                         "LAMP_CONTROL_HIGH"
    MENU_POSITION_BOTTOM_LEFT =                                 "MENU_POS_BOTTOM_LEFT"
    MENU_POSITION_CENTER =                                      "MENU_POS_CENTER"



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
        SimpleCommands.PICTURE_POSITION_SELECT_1_85: f"{ADCP.Commands.PICTURE_POSITION_SELECT.value} {ADCP.Values.PicturePositions.PP_1_85.value}",
        SimpleCommands.PICTURE_POSITION_SELECT_2_35: f"{ADCP.Commands.PICTURE_POSITION_SELECT.value} {ADCP.Values.PicturePositions.PP_2_35.value}",
        SimpleCommands.PICTURE_POSITION_SELECT_CUSTOM_1: f"{ADCP.Commands.PICTURE_POSITION_SELECT.value} {ADCP.Values.PicturePositions.CUSTOM1.value}",
        SimpleCommands.PICTURE_POSITION_SELECT_CUSTOM_2: f"{ADCP.Commands.PICTURE_POSITION_SELECT.value} {ADCP.Values.PicturePositions.CUSTOM2.value}",
        SimpleCommands.PICTURE_POSITION_SELECT_CUSTOM_3: f"{ADCP.Commands.PICTURE_POSITION_SELECT.value} {ADCP.Values.PicturePositions.CUSTOM3.value}",
        SimpleCommands.PICTURE_POSITION_SELECT_CUSTOM_4: f"{ADCP.Commands.PICTURE_POSITION_SELECT.value} {ADCP.Values.PicturePositions.CUSTOM4.value}",
        SimpleCommands.PICTURE_POSITION_SELECT_CUSTOM_5: f"{ADCP.Commands.PICTURE_POSITION_SELECT.value} {ADCP.Values.PicturePositions.CUSTOM5.value}",
        SimpleCommands.PICTURE_POSITION_SAVE_1_85: f"{ADCP.Commands.PICTURE_POSITION_SAVE.value} {ADCP.Values.PicturePositionsManage.PP_1_85.value}",
        SimpleCommands.PICTURE_POSITION_SAVE_2_35: f"{ADCP.Commands.PICTURE_POSITION_SAVE.value} {ADCP.Values.PicturePositionsManage.PP_2_35.value}",
        SimpleCommands.PICTURE_POSITION_SAVE_CUSTOM_1: f"{ADCP.Commands.PICTURE_POSITION_SAVE.value} {ADCP.Values.PicturePositionsManage.CUSTOM1.value}",
        SimpleCommands.PICTURE_POSITION_SAVE_CUSTOM_2: f"{ADCP.Commands.PICTURE_POSITION_SAVE.value} {ADCP.Values.PicturePositionsManage.CUSTOM2.value}",
        SimpleCommands.PICTURE_POSITION_SAVE_CUSTOM_3: f"{ADCP.Commands.PICTURE_POSITION_SAVE.value} {ADCP.Values.PicturePositionsManage.CUSTOM3.value}",
        SimpleCommands.PICTURE_POSITION_SAVE_CUSTOM_4: f"{ADCP.Commands.PICTURE_POSITION_SAVE.value} {ADCP.Values.PicturePositionsManage.CUSTOM4.value}",
        SimpleCommands.PICTURE_POSITION_SAVE_CUSTOM_5: f"{ADCP.Commands.PICTURE_POSITION_SAVE.value} {ADCP.Values.PicturePositionsManage.CUSTOM5.value}",
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



class MediaPlayer():
    """Media player entity definition class that includes the device class, features, attributes and options"""

    _device_class = ucapi.media_player.DeviceClasses.TV
    _features = [
        ucapi.media_player.Features.ON_OFF,
        ucapi.media_player.Features.TOGGLE,
        ucapi.media_player.Features.MUTE,
        ucapi.media_player.Features.UNMUTE,
        ucapi.media_player.Features.MUTE_TOGGLE,
        ucapi.media_player.Features.DPAD,
        ucapi.media_player.Features.HOME,
        ucapi.media_player.Features.SELECT_SOURCE
        ]
    _attributes = {
        ucapi.media_player.Attributes.STATE: ucapi.media_player.States.UNKNOWN,
        ucapi.media_player.Attributes.MUTED: False,
        ucapi.media_player.Attributes.SOURCE: "",
        ucapi.media_player.Attributes.SOURCE_LIST: [cmd.value for cmd in Sources]
        }
    _options = {
        ucapi.media_player.Options.SIMPLE_COMMANDS: [cmd.value for cmd in SimpleCommands]
        }

    def get_def(self, ent_id: str, name: str):
        """Returns the media player definition for the api call"""

        definition = ucapi.MediaPlayer(
            ent_id,
            name,
            features=MediaPlayer._features,
            attributes=MediaPlayer._attributes,
            device_class=MediaPlayer._device_class,
            options=MediaPlayer._options,
            cmd_handler=media_player.mp_cmd_handler
            )

        return definition



class Remote:
    """Remote entity definition class that includes the features, attributes and simple commands"""

    _features = [
        ucapi.remote.Features.ON_OFF,
        ucapi.remote.Features.TOGGLE,
        ]
    _attributes = {
        ucapi.remote.Attributes.STATE: ucapi.remote.States.UNKNOWN
        }
    _simple_commands = [cmd.value for cmd in SimpleCommands]

    def get_def(self, ent_id: str, name: str):
        """Returns the remote entity definition for the api call"""

        definition = ucapi.Remote(
            ent_id,
            name,
            features=Remote._features,
            attributes=Remote._attributes,
            simple_commands=Remote._simple_commands,
            button_mapping=remote.create_button_mappings(),
            ui_pages=remote.create_ui_pages(),
            cmd_handler=remote.remote_cmd_handler,
        )

        return definition



class LSTSensor:
    """Light source timer sensor entity definition class that includes the device class, attributes and options"""

    _device_class = ucapi.sensor.DeviceClasses.CUSTOM
    _attributes = {
        ucapi.sensor.Attributes.STATE: ucapi.sensor.States.ON,
        ucapi.sensor.Attributes.UNIT: "h"
        }
    _options = {
        ucapi.sensor.Options.CUSTOM_UNIT: "h"
        }

    def get_def(self, ent_id: str, name: str):
        """Returns the light source timer sensor entity definition for the api call"""

        definition = ucapi.Sensor(
            ent_id,
            name,
            features=None, #Mandatory although sensor entities have no features
            attributes=self._attributes,
            device_class=self._device_class,
            options=self._options
        )

        return definition



class PasswordManager:
    """Class to encrypt and decrypt the ADCP password."""

    @staticmethod
    def generate_salt() -> str:
        """Generate a unique salt from the hostname."""
        try:
            # Using the hostname to generate the salt seems to be the best compromise for an architecture independent method that works on all platforms, \
            # doesn't has to be stored somewhere and always returns the same value unless the hostname changes which the average user usually won't do. \
            # Getting the remotes serial using the additional WS core api is too complicated and also needs an api key or the pin code form the user
            unique_identifier = str(uuid.uuid5(uuid.NAMESPACE_DNS, socket.gethostname()))
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



#TODO Convert to ENUM class to reduce typos
class Setup:
    """Setup class which includes setup variables including functions to set() and get() them from a runtime storage
    which includes storing them in a json config file and as well as load() them from this file"""

    __conf = {
        "cfg_path": "config.json",
        "setup_masked_password": "******",
        "setup_complete": False, #Refers to the first time setup
        "setup_reconfigure": False,
        "setup_step": "init",
        "setup_auto_discovery": False,
        "setup_temp_device": "temp-device",
        "setup_reconfigure_device": "",
        "standby": False,
        "bundle_mode": False,
        "default_adcp_port": 53595,
        "default_adcp_timeout": 5,
        "default_sdap_port": 53862,
        "default_mp_poller_interval": 20,  # Use 0 to deactivate; will be automatically set to 0 when running on the remote (bundle_mode: True)
        "default_lt_poller_interval": 1800,  # Use 0 to deactivate
    }
    __setters = ["setup_complete", "setup_reconfigure", "setup_step", "setup_auto_discovery", "setup_reconfigure_device", \
                 "standby", "bundle_mode", "cfg_path", "default_mp_poller_interval", "default_lt_poller_interval"]
    __storers = ["setup_complete"]  # Skip runtime only related keys in config file

    @staticmethod
    def get(key):
        """Get the value from the specified key in __conf"""
        if key not in Setup.__conf:
            raise KeyError(f"Key \"{key}\" not found in setup configuration.")

        value = Setup.__conf[key]
        if value == "":
            raise ValueError(f"Got empty value for key \"{key}\" from runtime storage")

        return value

    @staticmethod
    def set(key, value, store: bool = True):
        """Set and store a value for the specified key into the runtime storage and config file."""

        if key in Setup.__setters:

            if Setup.__conf["setup_reconfigure"] and key == "setup_complete":
                _LOG.debug("Ignore setting and storing setup_complete flag during reconfiguration")

            else:

                Setup.__conf[key] = value
                _LOG.debug(f"Stored {key}: {value} into runtime storage")

                if not store:
                    _LOG.debug("Store set to False. Value will not be stored in config file this time")

                else:

                    if key in Setup.__storers:
                        if os.path.isfile(Setup.__conf["cfg_path"]):
                            try:
                                with open(Setup.__conf["cfg_path"], "r", encoding="utf-8") as f:
                                    existing_data = json.load(f)
                            except Exception as e:
                                _LOG.error(f"Failed to load existing config data: {e}")
                                existing_data = {}
                        else:
                            existing_data = {}

                        if not isinstance(existing_data, dict):
                            _LOG.error("Config file has an invalid structure. Expected a dictionary.")
                            existing_data = {}

                        if "setup" not in existing_data:
                            existing_data["setup"] = {}
                        existing_data["setup"][key] = value

                        try:
                            with open(Setup.__conf["cfg_path"], "w", encoding="utf-8") as f:
                                json.dump(existing_data, f, indent=4)
                            _LOG.debug(f"Stored {key}: {value} into {Setup.__conf['cfg_path']}")
                        except Exception as e:
                            raise Exception(f"Error while storing {key}: {value} into {Setup.__conf['cfg_path']}") from e

        else:
            raise NameError(f"{key} should not be changed")

    @staticmethod
    def load():
        """Load all variables from the config json file into the runtime storage"""

        if os.path.isfile(Setup.__conf["cfg_path"]):
            try:
                with open(Setup.__conf["cfg_path"], "r", encoding="utf-8") as f:
                    configfile = json.load(f)

                if not isinstance(configfile, dict):
                    raise ValueError("Config file has an invalid structure. Expected a dictionary.")

                if "setup" in configfile:
                    Setup.__conf.update(configfile["setup"])
                    _LOG.debug(f"Loaded setup data: {configfile['setup']} into runtime storage")
                else:
                    _LOG.warning("No 'setup' section found in config file. Using default values.")

            except Exception as e:
                raise OSError(f"Error while reading {Setup.__conf['cfg_path']}") from e
        else:
            _LOG.info(f"{Setup.__conf['cfg_path']} does not exist. Using default setup values.")



class Devices:
    """Class to manage multiple projector devices with all needed configuration data like entity id, ip, password etc.
    
    Includes methods to store them in runtime and saving/loading them from a config file."""

    __devices = []
    __temp_id = Setup.get("setup_temp_device")

    @staticmethod
    def get(device_id: str = None, key: str = None):
        """
        Get device by its media player entity ID. Optionally, retrieve a specific key's value.
        :param device_id: The entity ID of the device's media player/remote entity.
        :param key: (Optional) The specific key to retrieve from the device's data.
        :return: A dictionary containing the device configuration data or the value of the specified key.
        """
        if device_id is None:
            #If no device_id is provided {Devices.__temp_id} will be used instead
            device_id = Devices.__temp_id

        device = next((d for d in Devices.__devices if d.get("device_id") == device_id), None)
        if device is None:
            raise ValueError(f"Device with device ID \"{device_id}\" does not exist.")

        if key:
            if key not in device:
                return None
            if key == "adcp_password":
                salt = PasswordManager.generate_salt()
                decrypted_password = PasswordManager.decrypt_password(device[key], salt)
                return decrypted_password
            return device[key]

        return device

    @staticmethod
    def add(device_id: str = None, entity_data: dict = None, new_device_id: str = None):
        """
        Add or update a device. If no device_id is provided, store the data under a temporary ID.
        If a device_id is provided, merge the new data with the existing data.
        Optionally, update the device_id to a new value.

        :param device_id: (Optional) The current ID of the device.
        :param entity_data: A dictionary containing the device configuration data.
        :param new_device_id: (Optional) The new ID to assign to the device.
        """
        if entity_data is None:
            raise ValueError("entity_data cannot be None")

        if not isinstance(entity_data, dict):
            raise TypeError("entity_data must be a dictionary")

        if device_id is None:
            #If no device_id is provided {Devices.__temp_id} will be used instead
            device_id = Devices.__temp_id

        if "adcp_password" in entity_data:
            salt = PasswordManager.generate_salt()
            encrypted_password = PasswordManager.encrypt_password(entity_data["adcp_password"], salt)
            entity_data["adcp_password"] = encrypted_password
            _LOG.debug("Encrypted ADCP password before storing it in the device data")

        existing_device = next((d for d in Devices.__devices if d.get("device_id") == device_id), None)

        if existing_device:
            _LOG.debug(f"Adding entity_data {entity_data} to \"{device_id}\"")
            existing_device.update(entity_data)
        else:
            _LOG.debug(f"Adding new device with ID \"{device_id}\"")
            entity_data["device_id"] = device_id
            _LOG.debug(f"Adding entity_data: {entity_data}")
            Devices.__devices.append(entity_data)

        if new_device_id:
            if any(d.get("device_id") == new_device_id for d in Devices.__devices):
                raise ValueError(f"Device with ID \"{new_device_id}\" already exists")
            _LOG.debug(f"Updating device ID from \"{device_id}\" to \"{new_device_id}\"")
            existing_device["device_id"] = new_device_id

        Devices._save()

    @staticmethod
    def remove(device_id: str, key: str = None):
        """
        Remove a device or a specific key from a device by its media player/remote entity ID.
        Saves changes to the config file.
        :param device_id: The entity ID of the device's media player/remote entity.
        :param key: (Optional) The specific key to remove from the device's data.
        """

        device = next((d for d in Devices.__devices if d.get("device_id") == device_id), None)
        if device is None:
            raise ValueError(f"Device with device ID \"{device_id}\" does not exist")

        if key:
            if key not in device:
                raise KeyError(f"Key \"{key}\" does not exist for device with ID \"{device_id}\"")
            del device[key]
            _LOG.debug(f"Removed key \"{key}\" from device with ID \"{device_id}\"")
        else:
            Devices.__devices.remove(device)
            _LOG.debug(f"Removed device with ID \"{device_id}\"")

        Devices._save()

    @staticmethod
    def list() -> list:
        """
        List all device IDs.
        
        :return: A list of device IDs.
        """
        return [device["device_id"] for device in Devices.__devices]

    @staticmethod
    def _save():
        """
        Save all devices to the config file. Already included in add_entity and remove_entity.
        """
        try:
            cfg_path = Setup.get("cfg_path")
            if os.path.isfile(cfg_path):
                try:
                    with open(cfg_path, "r", encoding="utf-8") as f:
                        existing_data = json.load(f)
                except Exception as e:
                    _LOG.error(f"Failed to load existing config data: {e}")
                    existing_data = {}
            else:
                existing_data = {}

            if not isinstance(existing_data, dict):
                _LOG.error("Config file has an invalid structure. Expected a dictionary.")
                existing_data = {}

            existing_data["devices"] = Devices.__devices

            with open(cfg_path, "w", encoding="utf-8") as f:
                json.dump(existing_data, f, indent=4)
            _LOG.debug(f"Updated device data in {cfg_path}")
        except Exception as e:
            _LOG.error(f"Failed to save new device data to {cfg_path}: {e}")
            raise

    @staticmethod
    def load():
        """
        Load all devices from the config file into runtime storage.
        """
        cfg_path = Setup.get("cfg_path")
        if os.path.isfile(cfg_path):
            try:
                with open(cfg_path, "r", encoding="utf-8") as f:
                    data = json.load(f)

                if not isinstance(data, dict) or "devices" not in data:
                    raise ValueError("Config file has an invalid structure. Expected a dictionary with a \"devices\" key.")

                if not isinstance(data["devices"], list):
                    raise ValueError("The \"devices\" key in the config file must contain a list.")

                Devices.__devices = data["devices"]
                count = len(Devices.__devices)
                if count < 1:
                    _LOG.debug(f"No devices found in {cfg_path}")
                else:
                    _LOG.debug(f"Loaded {count} device(s) into runtime storage")
            except Exception as e:
                _LOG.error(f"Failed to load device data from {cfg_path}: {e}")
                Devices.__devices = []
        else:
            _LOG.info(f"{cfg_path} does not exist. No devices loaded.")
            Devices.__devices = []

    @staticmethod
    def set_remote_and_sensor_data(device_id: str):
        """Generate light source timer sensor entity id and name and store it"""

        _LOG.info("Generate remote id and light source timer sensor entity id and name")

        rt_id = "remote-" + device_id
        name = Devices.get(device_id=device_id, key="name")

        lt_entity_id = "lighttimer-" + device_id
        lt_entity_name = {
            "en": "Light source timer " + device_id,
            "de": "Lichtquellen-Timer " + name
        }

        data = {"rt-id": rt_id, "lt-id": lt_entity_id, "lt-name": lt_entity_name}
        try:
            Devices.add(device_id, entity_data=data)
        except ValueError as v:
            raise ValueError(v) from v
