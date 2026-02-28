"""This module contains the setup dataclasses and functions, entity definition classes and various mapping classes and functions"""

from enum import StrEnum
from dataclasses import dataclass, fields

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



@dataclass
class SetupSteps:
    """Defines all setup steps for the setup flow"""
    init: str = "init"
    action: str = "action"
    choose_device: str = "choose_device"
    basic: str = "basic"
    basic_reconfigure: str = "basic_reconfigure"
    advanced: str = "advanced"
    advanced_reconfigure: str = "advanced_reconfigure"

@dataclass
class SetupData:
    """Class to store all setup und runtime related data"""
    standby: bool = False
    bundle_mode: bool = False
    cfg_path: str = "config.json"
    default_adcp_port: int = 53595
    default_adcp_timeout: int = 5
    default_sdap_port: int = 53862
    default_poller_interval_media_player: int = 20
    default_poller_interval_health: int = 1800
    setup_complete: bool = False
    setup_reconfigure: bool = False
    setup_auto_discovery: bool  = False
    setup_step: str = SetupSteps.init
    setup_reconfigure_device: str = ""
    setup_password_masked: str = "******"
    setup_temp_device_name: str = "temp-device"

class Messages(StrEnum):
    #TODO Create different language specific message classes that will be used depending on what language the remote is set to (via ucapi call api.get_localization_cfg)
    """Defines all messages used as values in the integration"""
    TEMPORARILY_UNAVAILABLE = "Temporarily Unavailable"
    ERROR = "Error"
    NO_SIGNAL = "No Signal"
    VIDEO_MUTED = "Video Muted"
    NO_ERROR = "No Error"
    NO_WARNING = "No Warning"

class Sources (StrEnum):
    """Defines all sources for the media player entity"""
    HDMI_1 = "HDMI 1"
    HDMI_2 = "HDMI 2"
    UNKNOWN = "Unknown"

class SimpleCommands (StrEnum):
    """Defines all simple commands for the media player and remote entity.
    Maximum 20 upper case only characters including -/_.:+#*°@%()? allowed"""

    INPUT_HDMI1 =                                               "INPUT_HDMI_1"
    INPUT_HDMI2 =                                               "INPUT_HDMI_2"
    MODE_PRESET_REF =                                           "MODE_PIC_REF"
    MODE_PRESET_USER =                                          "MODE_PIC_USER"
    MODE_PRESET_USER1 =                                         "MODE_PIC_USER1"
    MODE_PRESET_USER2 =                                         "MODE_PIC_USER2"
    MODE_PRESET_USER3 =                                         "MODE_PIC_USER3"
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
    MODE_HDR_HDR10 =                                            "MODE_HDR_HDR10"
    MODE_HDR_HDR_REF =                                          "MODE_HDR_HDR_REF"
    MODE_HDR_HLG =                                              "MODE_HDR_HLG"
    MODE_HDR_DYNAMIC_TONE_MAPPING_1 =                           "MODE_HDR_TONEMAP_1"
    MODE_HDR_DYNAMIC_TONE_MAPPING_2 =                           "MODE_HDR_TONEMAP_2"
    MODE_HDR_DYNAMIC_TONE_MAPPING_3 =                           "MODE_HDR_TONEMAP_3"
    MODE_HDR_DYNAMIC_TONE_MAPPING_OFF =                         "MODE_HDR_TONEMAP_OFF"
    MODE_CONTRAST_ENHANCER_HIGH =                               "MODE_CONTR_ENHA_HIGH"
    MODE_CONTRAST_ENHANCER_MID =                                "MODE_CONTR_ENHA_MID"
    MODE_CONTRAST_ENHANCER_LOW =                                "MODE_CONTR_ENHA_LOW"
    MODE_CONTRAST_ENHANCER_OFF =                                "MODE_CONTR_ENHA_OFF"
    MODE_2D_3D_SELECT_AUTO =                                    "MODE_2D/3D_SEL_AUTO"
    MODE_2D_3D_SELECT_3D =                                      "MODE_2D/3D_SEL_3D"
    MODE_2D_3D_SELECT_2D =                                      "MODE_2D/3D_SEL_2D"
    MODE_3D_FORMAT_SIMULATED_3D =                               "MODE_3D_SIM_3D"
    MODE_3D_FORMAT_SIDE_BY_SIDE =                               "MODE_3D_SIDE_BY_SIDE"
    MODE_3D_FORMAT_OVER_UNDER =                                 "MODE_3D_OVER_UNDER"
    MODE_DYNAMIC_IRIS_CONTROL_OFF =                             "MODE_DYN_IRIS_OFF"
    MODE_DYNAMIC_IRIS_CONTROL_FULL =                            "MODE_DYN_IRIS_FULL"
    MODE_DYNAMIC_IRIS_CONTROL_LIMITED =                         "MODE_DYN_IRIS_LIM"
    MODE_DYNAMIC_LIGHT_CONTROL_OFF =                            "MODE_DYN_LIGHT_OFF"
    MODE_DYNAMIC_LIGHT_CONTROL_FULL =                           "MODE_DYN_LIGHT_FULL"
    MODE_DYNAMIC_LIGHT_CONTROL_LIMITED =                        "MODE_DYN_LIGHT_LIM"
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
    LASER_BRIGHTNESS_UP =                                       "LASER_DIM_UP"
    LASER_BRIGHTNESS_DOWN =                                     "LASER_DIM_DOWN"
    IRIS_BRIGHTNESS_UP =                                        "IRIS_BRIGHTNESS_UP"
    IRIS_BRIGHTNESS_DOWN =                                      "IRIS_BRIGHTNESS_DOWN"
    LAMP_CONTROL_LOW =                                          "LAMP_CONTROL_LOW"
    LAMP_CONTROL_HIGH =                                         "LAMP_CONTROL_HIGH"
    MENU_POSITION_BOTTOM_LEFT =                                 "MENU_POS_BOTTOM_LEFT"
    MENU_POSITION_CENTER =                                      "MENU_POS_CENTER"
    UPDATE_VIDEO_INFO =                                         "UPDATE_VIDEO_INFO"
    UPDATE_HEALTH_STATUS =                                      "UPDATE_HEALTH_STATUS"
    UPDATE_ALL_SENSORS =                                        "UPDATE_ALL_SENSORS"
    UPDATE_SELECT_OPTIONS =                                     "UPDATE_SELECT_OPTION"

class SensorVideoSignalTypes (StrEnum):
    """
    Defines all setting types needed for the video signal sensor.
    These are separated from the other sensor types as they are combined in the video signal sensor and need to be queried separately
    Color Space and 2d/3d mode are settings and included in SensorTypes
    """
    RESOLUTION = "resolution"
    DYNAMIC_RANGE = "dynamic-range"
    COLOR_FORMAT = "color-format"

class SensorSystemStatusTypes (StrEnum):
    """
    Defines all setting types needed for the system status sensor.
    These are separated from the other sensor types as they are combined in the system status sensor and need to be queried separately
    """
    ERROR = "error"
    WARNING = "warning"

class SensorTypes (StrEnum):
    """Defines all setting types that can be queried from the projector and used for sensors in the integration"""
    VIDEO_SIGNAL = "video"
    TEMPERATURE = "temp"
    LIGHT_TIMER = "light"
    SYSTEM_STATUS = "system"
    POWER_STATUS = "power-status"
    INPUT = "input"
    PICTURE_MUTING = "picture-muting"
    PICTURE_PRESET = "picture-preset"
    ASPECT = "aspect"
    PICTURE_POSITION_SELECT = "picture-position"
    HDR_STATUS = "hdr-status"
    HDR_DYNAMIC_TONE_MAPPING = "hdr-dynamic-tone-mapping"
    LAMP_CONTROL = "lamp-control"
    DYNAMIC_IRIS_CONTROL = "dynamic-iris-control"
    DYNAMIC_LIGHT_CONTROL = "dynamic-light-control"
    MOTIONFLOW = "motionflow"
    FORMAT_3D = "3d-format"
    INPUT_LAG_REDUCTION = "input-lag-reduction"
    MENU_POSITION = "menu-position"
    COLOR_TEMPERATURE = "color-temperature"
    COLOR_SPACE = "color-space"
    GAMMA = "gamma"
    CONTRAST_ENHANCER = "contrast-enhancer"
    MODE_2D_3D = "2d/3d-mode"
    LASER_BRIGHTNESS = "laser-brightness"
    IRIS_BRIGHTNESS = "iris-brightness"

    @staticmethod
    def get_all():
        """Get a list of all sensor types defined in this class"""
        values = [member for member in SensorTypes]

        return values

class SelectTypes (StrEnum):
    """Defines all setting types that can be set with select commands and need to be queried for their options"""
    POWER = "power" #No query possible. Use power-status ? instead which is query only
    INPUT = "input"
    PICTURE_MUTING = "picture-muting"
    PICTURE_PRESET = "picture-preset"
    ASPECT = "aspect"
    PICTURE_POSITION_SELECT = "picture-position-select"
    PICTURE_POSITION_SAVE = "picture-position-save"
    HDR_FORMAT = "hdr-format"
    HDR_DYNAMIC_TONE_MAPPING = "hdr-dynamic-tone-mapping"
    LAMP_CONTROL = "lamp-control"
    DYNAMIC_IRIS_CONTROL = "dynamic-iris-control"
    DYNAMIC_LIGHT_CONTROL = "dynamic-light-control"
    MOTIONFLOW = "motionflow"
    FORMAT_3D = "3d-format"
    INPUT_LAG_REDUCTION = "input-lag-reduction"
    MENU_POSITION = "menu-position"
    COLOR_TEMPERATURE = "color-temperature"
    COLOR_SPACE = "color-space"
    GAMMA = "gamma"
    CONTRAST_ENHANCER = "contrast-enhancer"

    @staticmethod
    def get_all():
        """Get a list of all select types defined in this class"""
        values = [member for member in SelectTypes]

        return values



class UC2ADCP:
    """Maps entity commands to ADCP commands"""

    __cmd_map = {
        #ADCP key commands
        ucapi.media_player.Commands.TOGGLE: ADCP.Commands.Key.POWER_TOGGLE,
        ucapi.media_player.Commands.HOME: ADCP.Commands.Key.MENU,
        ucapi.media_player.Commands.MENU: ADCP.Commands.Key.MENU,
        ucapi.media_player.Commands.BACK: ADCP.Commands.Key.LEFT,
        ucapi.media_player.Commands.CURSOR_UP: ADCP.Commands.Key.UP,
        ucapi.media_player.Commands.CURSOR_DOWN: ADCP.Commands.Key.DOWN,
        ucapi.media_player.Commands.CURSOR_LEFT: ADCP.Commands.Key.LEFT,
        ucapi.media_player.Commands.CURSOR_RIGHT: ADCP.Commands.Key.RIGHT,
        ucapi.media_player.Commands.CURSOR_ENTER: ADCP.Commands.Key.ENTER,
        SimpleCommands.LENS_SHIFT_UP: ADCP.Commands.Key.LENS_SHIFT_UP,
        SimpleCommands.LENS_SHIFT_DOWN: ADCP.Commands.Key.LENS_SHIFT_DOWN,
        SimpleCommands.LENS_SHIFT_LEFT: ADCP.Commands.Key.LENS_SHIFT_LEFT,
        SimpleCommands.LENS_SHIFT_RIGHT: ADCP.Commands.Key.LENS_SHIFT_RIGHT,
        SimpleCommands.LENS_FOCUS_FAR: ADCP.Commands.Key.LENS_FOCUS_FAR,
        SimpleCommands.LENS_FOCUS_NEAR: ADCP.Commands.Key.LENS_FOCUS_NEAR,
        SimpleCommands.LENS_ZOOM_LARGE: ADCP.Commands.Key.LENS_ZOOM_LARGE,
        SimpleCommands.LENS_ZOOM_SMALL: ADCP.Commands.Key.LENS_ZOOM_SMALL,
        #ADCP select commands
        ucapi.media_player.Commands.ON: f"{ADCP.Commands.Select.POWER} {ADCP.Values.States.ON}",
        ucapi.media_player.Commands.OFF: f"{ADCP.Commands.Select.POWER} {ADCP.Values.States.OFF}",
        ucapi.media_player.Commands.MUTE: f"{ADCP.Commands.Select.MUTE} {ADCP.Values.States.ON}",
        ucapi.media_player.Commands.UNMUTE: f"{ADCP.Commands.Select.MUTE} {ADCP.Values.States.OFF}",
        SimpleCommands.INPUT_HDMI1: f"{ADCP.Commands.Select.INPUT} {ADCP.Values.Inputs.HDMI1}",
        SimpleCommands.INPUT_HDMI2: f"{ADCP.Commands.Select.INPUT} {ADCP.Values.Inputs.HDMI2}",
        SimpleCommands.MODE_PRESET_BRIGHT_CINEMA: f"{ADCP.Commands.Select.PICTURE_MODE} {ADCP.Values.PictureModes.BRIGHT_CINEMA}",
        SimpleCommands.MODE_PRESET_BRIGHT_TV: f"{ADCP.Commands.Select.PICTURE_MODE} {ADCP.Values.PictureModes.BRIGHT_TV}",
        SimpleCommands.MODE_PRESET_CINEMA_FILM_1: f"{ADCP.Commands.Select.PICTURE_MODE} {ADCP.Values.PictureModes.CINEMA_FILM1}",
        SimpleCommands.MODE_PRESET_CINEMA_FILM_2: f"{ADCP.Commands.Select.PICTURE_MODE} {ADCP.Values.PictureModes.CINEMA_FILM2}",
        SimpleCommands.MODE_PRESET_REF: f"{ADCP.Commands.Select.PICTURE_MODE} {ADCP.Values.PictureModes.REFERENCE}",
        SimpleCommands.MODE_PRESET_TV: f"{ADCP.Commands.Select.PICTURE_MODE} {ADCP.Values.PictureModes.TV}",
        SimpleCommands.MODE_PRESET_PHOTO: f"{ADCP.Commands.Select.PICTURE_MODE} {ADCP.Values.PictureModes.PHOTO}",
        SimpleCommands.MODE_PRESET_GAME: f"{ADCP.Commands.Select.PICTURE_MODE} {ADCP.Values.PictureModes.GAME}",
        SimpleCommands.MODE_PRESET_USER: f"{ADCP.Commands.Select.PICTURE_MODE} {ADCP.Values.PictureModes.USER}",
        SimpleCommands.MODE_PRESET_USER1: f"{ADCP.Commands.Select.PICTURE_MODE} {ADCP.Values.PictureModes.USER1}",
        SimpleCommands.MODE_PRESET_USER2: f"{ADCP.Commands.Select.PICTURE_MODE} {ADCP.Values.PictureModes.USER2}",
        SimpleCommands.MODE_PRESET_USER3: f"{ADCP.Commands.Select.PICTURE_MODE} {ADCP.Values.PictureModes.USER3}",
        SimpleCommands.MODE_ASPECT_RATIO_NORMAL: f"{ADCP.Commands.Select.ASPECT} {ADCP.Values.Aspect.NORMAL}",
        SimpleCommands.MODE_ASPECT_RATIO_V_STRETCH: f"{ADCP.Commands.Select.ASPECT} {ADCP.Values.Aspect.V_STRETCH}",
        SimpleCommands.MODE_ASPECT_RATIO_ZOOM_1_85: f"{ADCP.Commands.Select.ASPECT} {ADCP.Values.Aspect.ZOOM_1_85}",
        SimpleCommands.MODE_ASPECT_RATIO_ZOOM_2_35: f"{ADCP.Commands.Select.ASPECT} {ADCP.Values.Aspect.ZOOM_2_35}",
        SimpleCommands.MODE_ASPECT_RATIO_STRETCH: f"{ADCP.Commands.Select.ASPECT} {ADCP.Values.Aspect.STRETCH}",
        SimpleCommands.MODE_ASPECT_RATIO_SQUEEZE: f"{ADCP.Commands.Select.ASPECT} {ADCP.Values.Aspect.SQUEEZE}",
        SimpleCommands.MODE_MOTIONFLOW_OFF: f"{ADCP.Commands.Select.MOTIONFLOW} {ADCP.Values.Motionflow.OFF}",
        SimpleCommands.MODE_MOTIONFLOW_COMBINATION: f"{ADCP.Commands.Select.MOTIONFLOW} {ADCP.Values.Motionflow.COMBINATION}",
        SimpleCommands.MODE_MOTIONFLOW_SMOOTH_HIGH: f"{ADCP.Commands.Select.MOTIONFLOW} {ADCP.Values.Motionflow.SMOOTH_HIGH}",
        SimpleCommands.MODE_MOTIONFLOW_SMOOTH_LOW: f"{ADCP.Commands.Select.MOTIONFLOW} {ADCP.Values.Motionflow.SMOOTH_LOW}",
        SimpleCommands.MODE_MOTIONFLOW_IMPULSE: f"{ADCP.Commands.Select.MOTIONFLOW} {ADCP.Values.Motionflow.IMPULSE}",
        SimpleCommands.MODE_MOTIONFLOW_TRUE_CINEMA: f"{ADCP.Commands.Select.MOTIONFLOW} {ADCP.Values.Motionflow.TRUE_CINEMA}",
        SimpleCommands.MODE_HDR_ON: f"{ADCP.Commands.Select.HDR} {ADCP.Values.HDR.ON}",
        SimpleCommands.MODE_HDR_OFF: f"{ADCP.Commands.Select.HDR} {ADCP.Values.HDR.OFF}",
        SimpleCommands.MODE_HDR_AUTO: f"{ADCP.Commands.Select.HDR} {ADCP.Values.HDR.AUTO}",
        SimpleCommands.MODE_HDR_HDR10: f"{ADCP.Commands.Select.HDR} {ADCP.Values.HDR.HDR10}",
        SimpleCommands.MODE_HDR_HDR_REF: f"{ADCP.Commands.Select.HDR} {ADCP.Values.HDR.HDR_REF}",
        SimpleCommands.MODE_HDR_HLG: f"{ADCP.Commands.Select.HDR} {ADCP.Values.HDR.HLG}",
        SimpleCommands.MODE_HDR_DYNAMIC_TONE_MAPPING_1: f"{ADCP.Commands.Select.HDR_DYNAMIC_TONE_MAPPING} {ADCP.Values.HDRDynToneMapping.MODE_1}",
        SimpleCommands.MODE_HDR_DYNAMIC_TONE_MAPPING_2: f"{ADCP.Commands.Select.HDR_DYNAMIC_TONE_MAPPING} {ADCP.Values.HDRDynToneMapping.MODE_2}",
        SimpleCommands.MODE_HDR_DYNAMIC_TONE_MAPPING_3: f"{ADCP.Commands.Select.HDR_DYNAMIC_TONE_MAPPING} {ADCP.Values.HDRDynToneMapping.MODE_3}",
        SimpleCommands.MODE_HDR_DYNAMIC_TONE_MAPPING_OFF: f"{ADCP.Commands.Select.HDR_DYNAMIC_TONE_MAPPING} {ADCP.Values.HDRDynToneMapping.OFF}",
        SimpleCommands.MODE_2D_3D_SELECT_AUTO: f"{ADCP.Commands.Select.MODE_2D_3D} {ADCP.Values.Mode2D3D.MODE_AUTO}",
        SimpleCommands.MODE_2D_3D_SELECT_3D: f"{ADCP.Commands.Select.MODE_2D_3D} {ADCP.Values.Mode2D3D.MODE_3D}",
        SimpleCommands.MODE_2D_3D_SELECT_2D: f"{ADCP.Commands.Select.MODE_2D_3D} {ADCP.Values.Mode2D3D.MODE_2D}",
        SimpleCommands.MODE_3D_FORMAT_SIMULATED_3D: f"{ADCP.Commands.Select.MODE_3D_FORMAT} {ADCP.Values.Mode3DFormat.SIMULATED}",
        SimpleCommands.MODE_3D_FORMAT_SIDE_BY_SIDE: f"{ADCP.Commands.Select.MODE_3D_FORMAT} {ADCP.Values.Mode3DFormat.SIDE_BY_SIDE}",
        SimpleCommands.MODE_3D_FORMAT_OVER_UNDER: f"{ADCP.Commands.Select.MODE_3D_FORMAT} {ADCP.Values.Mode3DFormat.OVER_UNDER}",
        SimpleCommands.MODE_DYNAMIC_IRIS_CONTROL_OFF: f"{ADCP.Commands.Select.DYNAMIC_IRIS_CONTROL} {ADCP.Values.LightControl.OFF}",
        SimpleCommands.MODE_DYNAMIC_IRIS_CONTROL_FULL: f"{ADCP.Commands.Select.DYNAMIC_IRIS_CONTROL} {ADCP.Values.LightControl.FULL}",
        SimpleCommands.MODE_DYNAMIC_IRIS_CONTROL_LIMITED: f"{ADCP.Commands.Select.DYNAMIC_IRIS_CONTROL} {ADCP.Values.LightControl.LIMITED}",
        SimpleCommands.MODE_DYNAMIC_LIGHT_CONTROL_OFF: f"{ADCP.Commands.Select.DYNAMIC_LIGHT_CONTROL} {ADCP.Values.LightControl.OFF}",
        SimpleCommands.MODE_DYNAMIC_LIGHT_CONTROL_FULL: f"{ADCP.Commands.Select.DYNAMIC_LIGHT_CONTROL} {ADCP.Values.LightControl.FULL}",
        SimpleCommands.MODE_DYNAMIC_LIGHT_CONTROL_LIMITED: f"{ADCP.Commands.Select.DYNAMIC_LIGHT_CONTROL} {ADCP.Values.LightControl.LIMITED}",
        SimpleCommands.MODE_CONTRAST_ENHANCER_OFF: f"{ADCP.Commands.Select.CONTRAST_ENHANCER} {ADCP.Values.ContrastEnhancer.OFF}",
        SimpleCommands.MODE_CONTRAST_ENHANCER_LOW: f"{ADCP.Commands.Select.CONTRAST_ENHANCER} {ADCP.Values.ContrastEnhancer.LOW}",
        SimpleCommands.MODE_CONTRAST_ENHANCER_MID: f"{ADCP.Commands.Select.CONTRAST_ENHANCER} {ADCP.Values.ContrastEnhancer.MID}",
        SimpleCommands.MODE_CONTRAST_ENHANCER_HIGH: f"{ADCP.Commands.Select.CONTRAST_ENHANCER} {ADCP.Values.ContrastEnhancer.HIGH}",
        SimpleCommands.PICTURE_POSITION_SELECT_1_85: f"{ADCP.Commands.Select.PICTURE_POSITION_SELECT} {ADCP.Values.PicturePositions.PP_1_85}",
        SimpleCommands.PICTURE_POSITION_SELECT_2_35: f"{ADCP.Commands.Select.PICTURE_POSITION_SELECT} {ADCP.Values.PicturePositions.PP_2_35}",
        SimpleCommands.PICTURE_POSITION_SELECT_CUSTOM_1: f"{ADCP.Commands.Select.PICTURE_POSITION_SELECT} {ADCP.Values.PicturePositions.CUSTOM1}",
        SimpleCommands.PICTURE_POSITION_SELECT_CUSTOM_2: f"{ADCP.Commands.Select.PICTURE_POSITION_SELECT} {ADCP.Values.PicturePositions.CUSTOM2}",
        SimpleCommands.PICTURE_POSITION_SELECT_CUSTOM_3: f"{ADCP.Commands.Select.PICTURE_POSITION_SELECT} {ADCP.Values.PicturePositions.CUSTOM3}",
        SimpleCommands.PICTURE_POSITION_SELECT_CUSTOM_4: f"{ADCP.Commands.Select.PICTURE_POSITION_SELECT} {ADCP.Values.PicturePositions.CUSTOM4}",
        SimpleCommands.PICTURE_POSITION_SELECT_CUSTOM_5: f"{ADCP.Commands.Select.PICTURE_POSITION_SELECT} {ADCP.Values.PicturePositions.CUSTOM5}",
        SimpleCommands.PICTURE_POSITION_SAVE_1_85: f"{ADCP.Commands.Execute.PICTURE_POSITION_SAVE} {ADCP.Values.PicturePositionsManage.PP_1_85}",
        SimpleCommands.PICTURE_POSITION_SAVE_2_35: f"{ADCP.Commands.Execute.PICTURE_POSITION_SAVE} {ADCP.Values.PicturePositionsManage.PP_2_35}",
        SimpleCommands.PICTURE_POSITION_SAVE_CUSTOM_1: f"{ADCP.Commands.Execute.PICTURE_POSITION_SAVE} {ADCP.Values.PicturePositionsManage.CUSTOM1}",
        SimpleCommands.PICTURE_POSITION_SAVE_CUSTOM_2: f"{ADCP.Commands.Execute.PICTURE_POSITION_SAVE} {ADCP.Values.PicturePositionsManage.CUSTOM2}",
        SimpleCommands.PICTURE_POSITION_SAVE_CUSTOM_3: f"{ADCP.Commands.Execute.PICTURE_POSITION_SAVE} {ADCP.Values.PicturePositionsManage.CUSTOM3}",
        SimpleCommands.PICTURE_POSITION_SAVE_CUSTOM_4: f"{ADCP.Commands.Execute.PICTURE_POSITION_SAVE} {ADCP.Values.PicturePositionsManage.CUSTOM4}",
        SimpleCommands.PICTURE_POSITION_SAVE_CUSTOM_5: f"{ADCP.Commands.Execute.PICTURE_POSITION_SAVE} {ADCP.Values.PicturePositionsManage.CUSTOM5}",
        SimpleCommands.LAMP_CONTROL_LOW: f"{ADCP.Commands.Select.LAMP_CONTROL} {ADCP.Values.LampControl.LOW}",
        SimpleCommands.LAMP_CONTROL_HIGH: f"{ADCP.Commands.Select.LAMP_CONTROL} {ADCP.Values.LampControl.HIGH}",
        SimpleCommands.INPUT_LAG_REDUCTION_ON: f"{ADCP.Commands.Select.INPUT_LAG_REDUCTION} {ADCP.Values.States.ON}",
        SimpleCommands.INPUT_LAG_REDUCTION_OFF: f"{ADCP.Commands.Select.INPUT_LAG_REDUCTION} {ADCP.Values.States.OFF}",
        SimpleCommands.MENU_POSITION_BOTTOM_LEFT: f"{ADCP.Commands.Select.MENU_POSITION} {ADCP.Values.MenuPosition.BOTTOM_LEFT}",
        SimpleCommands.MENU_POSITION_CENTER: f"{ADCP.Commands.Select.MENU_POSITION} {ADCP.Values.MenuPosition.CENTER}",
        #ADCP numeric commands
        SimpleCommands.LASER_BRIGHTNESS_UP: f"{ADCP.Commands.Numeric.LASER_BRIGHTNESS} {ADCP.Parameters.RELATIVE} +10",
        SimpleCommands.LASER_BRIGHTNESS_DOWN: f"{ADCP.Commands.Numeric.LASER_BRIGHTNESS} {ADCP.Parameters.RELATIVE} -10",
        SimpleCommands.IRIS_BRIGHTNESS_UP: f"{ADCP.Commands.Numeric.IRIS_BRIGHTNESS} {ADCP.Parameters.RELATIVE} +10",
        SimpleCommands.IRIS_BRIGHTNESS_DOWN: f"{ADCP.Commands.Numeric.IRIS_BRIGHTNESS} {ADCP.Parameters.RELATIVE} -10",
        #Setting sensor commands
            #Query commands
            SensorTypes.POWER_STATUS : ADCP.Commands.Query.POWER_STATUS,
            SensorTypes.TEMPERATURE : ADCP.Commands.Query.TEMPERATURE,
            SensorTypes.LIGHT_TIMER : ADCP.Commands.Query.TIMER,
            SensorTypes.MODE_2D_3D : ADCP.Commands.Query.MODE_2D_3D, #returns 2d on newer 2d only models
            SensorVideoSignalTypes.RESOLUTION : ADCP.Commands.Query.SIGNAL,
            SensorVideoSignalTypes.DYNAMIC_RANGE : ADCP.Commands.Query.HDR_FORMAT,
            SensorVideoSignalTypes.COLOR_FORMAT : ADCP.Commands.Query.COLOR_FORMAT,
            SensorSystemStatusTypes.ERROR : ADCP.Commands.Query.ERROR,
            SensorSystemStatusTypes.WARNING : ADCP.Commands.Query.WARNING,
            #Select commands
            SensorTypes.INPUT : ADCP.Commands.Select.INPUT,
            SensorTypes.PICTURE_MUTING: ADCP.Commands.Select.MUTE,
            SensorTypes.PICTURE_PRESET : ADCP.Commands.Select.PICTURE_MODE,
            SensorTypes.ASPECT : ADCP.Commands.Select.ASPECT,
            SensorTypes.MOTIONFLOW : ADCP.Commands.Select.MOTIONFLOW,
            SensorTypes.INPUT_LAG_REDUCTION : ADCP.Commands.Select.INPUT_LAG_REDUCTION,
            SensorTypes.MENU_POSITION : ADCP.Commands.Select.MENU_POSITION,
            SensorTypes.COLOR_TEMPERATURE : ADCP.Commands.Select.COLOR_TEMPERATURE,
            SensorTypes.COLOR_SPACE : ADCP.Commands.Select.COLOR_SPACE,
            SensorTypes.GAMMA : ADCP.Commands.Select.GAMMA,
            SensorTypes.CONTRAST_ENHANCER : ADCP.Commands.Select.CONTRAST_ENHANCER,
            #Lamp models
            SensorTypes.LAMP_CONTROL: ADCP.Commands.Select.LAMP_CONTROL,
                #Iris only
                SensorTypes.DYNAMIC_IRIS_CONTROL : ADCP.Commands.Select.DYNAMIC_IRIS_CONTROL,
                SensorTypes.IRIS_BRIGHTNESS : ADCP.Commands.Numeric.IRIS_BRIGHTNESS,
            #Picture position models
            SensorTypes.PICTURE_POSITION_SELECT: ADCP.Commands.Select.PICTURE_POSITION_SELECT,
            #3D models
            SensorTypes.FORMAT_3D : ADCP.Commands.Select.MODE_3D_FORMAT,
            #HDR models
            SensorTypes.HDR_STATUS : ADCP.Commands.Select.HDR,
            SensorTypes.HDR_DYNAMIC_TONE_MAPPING : ADCP.Commands.Select.HDR_DYNAMIC_TONE_MAPPING, #only models never than xw6100/xw8100
            #Laser models
            SensorTypes.LASER_BRIGHTNESS : ADCP.Commands.Numeric.LASER_BRIGHTNESS,
            SensorTypes.DYNAMIC_LIGHT_CONTROL : ADCP.Commands.Select.DYNAMIC_LIGHT_CONTROL,
        #Select entity commands
        SelectTypes.POWER : ADCP.Commands.Select.POWER,
        SelectTypes.INPUT : ADCP.Commands.Select.INPUT,
        SelectTypes.PICTURE_MUTING: ADCP.Commands.Select.MUTE,
        SelectTypes.PICTURE_PRESET : ADCP.Commands.Select.PICTURE_MODE,
        SelectTypes.ASPECT : ADCP.Commands.Select.ASPECT,
        SelectTypes.MOTIONFLOW : ADCP.Commands.Select.MOTIONFLOW,
        SelectTypes.INPUT_LAG_REDUCTION : ADCP.Commands.Select.INPUT_LAG_REDUCTION,
        SelectTypes.MENU_POSITION : ADCP.Commands.Select.MENU_POSITION,
        SelectTypes.COLOR_TEMPERATURE : ADCP.Commands.Select.COLOR_TEMPERATURE,
        SelectTypes.COLOR_SPACE : ADCP.Commands.Select.COLOR_SPACE,
        SelectTypes.GAMMA : ADCP.Commands.Select.GAMMA,
        SelectTypes.CONTRAST_ENHANCER : ADCP.Commands.Select.CONTRAST_ENHANCER, #HDR: Dynamic HDR enhancer
        #Lamp models
        SelectTypes.LAMP_CONTROL: ADCP.Commands.Select.LAMP_CONTROL,
        SelectTypes.DYNAMIC_IRIS_CONTROL : ADCP.Commands.Select.DYNAMIC_IRIS_CONTROL,
        #Picture position models
        SelectTypes.PICTURE_POSITION_SELECT: ADCP.Commands.Select.PICTURE_POSITION_SELECT,
        SelectTypes.PICTURE_POSITION_SAVE : ADCP.Commands.Execute.PICTURE_POSITION_SAVE, #No range possible, use select command
        #3D models
        SelectTypes.FORMAT_3D : ADCP.Commands.Select.MODE_3D_FORMAT,
        #HDR models
        SelectTypes.HDR_FORMAT : ADCP.Commands.Select.HDR,
        SelectTypes.HDR_DYNAMIC_TONE_MAPPING : ADCP.Commands.Select.HDR_DYNAMIC_TONE_MAPPING, #only models never than xw6100/xw8100
        #Laser models
        SelectTypes.DYNAMIC_LIGHT_CONTROL : ADCP.Commands.Select.DYNAMIC_LIGHT_CONTROL
    }

    @staticmethod
    def get(key):
        """Get the ADCP command for the given key"""
        try:
            value = UC2ADCP.__cmd_map[key]

            if value == "":
                raise ValueError(f"Got empty value for key {key}")

            if hasattr(value, "value"):
                return value.value

            return value

        except KeyError as k:
            raise KeyError(f"Couldn't find a matching ADCP command for command {key}") from k


class EntityDefinitions:
    """Class to define the entity definitions for the api calls"""

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
            ucapi.media_player.Attributes.SOURCE_LIST: list(Sources)
            }
        _options = {
            ucapi.media_player.Options.SIMPLE_COMMANDS: list(SimpleCommands)
            }

        def get_def(self, ent_id: str, name: str):
            """Returns the media player definition for the api call"""

            definition = ucapi.MediaPlayer(
                ent_id,
                name,
                features=EntityDefinitions.MediaPlayer._features,
                attributes=EntityDefinitions.MediaPlayer._attributes,
                device_class=EntityDefinitions.MediaPlayer._device_class,
                options=EntityDefinitions.MediaPlayer._options,
                cmd_handler=media_player.cmd_handler
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
        _simple_commands = [cmd for cmd in SimpleCommands]

        def get_def(self, ent_id: str, name: str):
            """Returns the remote entity definition for the api call"""

            definition = ucapi.Remote(
                ent_id,
                name,
                features=EntityDefinitions.Remote._features,
                attributes=EntityDefinitions.Remote._attributes,
                simple_commands=EntityDefinitions.Remote._simple_commands,
                button_mapping=remote.create_button_mappings(),
                ui_pages=remote.create_ui_pages(),
                cmd_handler=remote.cmd_handler,
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
            # Maybe use the remote serial in the future when the system api command has been implemented in the Python ucapi
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
        try:
            key = PasswordManager._generate_key(salt)
            encrypted = base64.b64decode(encrypted_password)
            decrypted = bytes([e ^ key[i % len(key)] for i, e in enumerate(encrypted)])
            return decrypted.decode()
        except (UnicodeDecodeError, ValueError) as e:
            raise OSError(f"Failed to decrypt ADCP password: {e}") from e



class Setup:
    """Setup class which includes functions to set() and get() them from a runtime storage
    which includes storing them in a json config file and as well as load() them from this file"""

    # Runtime storage instance
    _data = SetupData()

    class Keys:
        """Defines all keys that can be set and stored in the setup configuration"""
        STANDBY = "standby"
        BUNDLE_MODE = "bundle_mode"
        CFG_PATH = "cfg_path"
        DEFAULT_POLLER_INTERVAL_MEDIA_PLAYER = "default_poller_interval_media_player"
        DEFAULT_POLLER_INTERVAL_HEALTH = "default_poller_interval_health"
        DEFAULT_ADCP_PORT = "default_adcp_port"
        DEFAULT_ADCP_TIMEOUT = "default_adcp_timeout"
        DEFAULT_SDAP_PORT = "default_sdap_port"
        SETUP_COMPLETE = "setup_complete"
        SETUP_RECONFIGURE = "setup_reconfigure"
        SETUP_STEP = "setup_step"
        SETUP_AUTO_DISCOVERY = "setup_auto_discovery"
        SETUP_RECONFIGURE_DEVICE = "setup_reconfigure_device"
        SETUP_PASSWORD_MASKED = "setup_password_masked"
        SETUP_TEMP_DEVICE_NAME = "setup_temp_device_name"

    __setters = [
        Keys.STANDBY,
        Keys.BUNDLE_MODE,
        Keys.CFG_PATH,
        Keys.DEFAULT_POLLER_INTERVAL_MEDIA_PLAYER,
        Keys.DEFAULT_POLLER_INTERVAL_HEALTH,
        Keys.SETUP_COMPLETE,
        Keys.SETUP_RECONFIGURE,
        Keys.SETUP_STEP,
        Keys.SETUP_AUTO_DISCOVERY,
        Keys.SETUP_RECONFIGURE_DEVICE,
    ]

    __storers = [Keys.SETUP_COMPLETE]  # Skip runtime only related keys in config file

    @staticmethod
    def get(key):
        """Get the value from the specified key in runtime dataclass storage"""
        if not hasattr(Setup._data, key):
            raise KeyError(f"Key \"{key}\" not found in setup configuration.")

        value = getattr(Setup._data, key)
        if value == "":
            raise ValueError(f"Got empty value for key \"{key}\" from runtime storage")

        return value

    @staticmethod
    def set(key, value, store: bool = True):
        """Set and store a value for the specified key into the runtime storage and config file."""

        if key in Setup.__setters:

            if getattr(Setup._data, Setup.Keys.SETUP_RECONFIGURE, False) and key == Setup.Keys.SETUP_COMPLETE:
                _LOG.debug("Ignore setting and storing setup_complete flag during reconfiguration")
                return

            # Only allow valid setup steps
            if key == Setup.Keys.SETUP_STEP:
                allowed_steps = [getattr(SetupSteps, f.name) for f in fields(SetupSteps)]
                if value not in allowed_steps:
                    raise ValueError(f"Invalid setup step '{value}'. Allowed: {sorted(allowed_steps)}")

            setattr(Setup._data, key, value)
            _LOG.debug(f"Stored {key}: {value} into runtime storage")

            if not store:
                _LOG.debug("Store set to False. Value will not be stored in config file this time")
                return

            if key in Setup.__storers:
                cfg_path = Setup._data.cfg_path
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

                if "setup" not in existing_data:
                    existing_data["setup"] = {}
                existing_data["setup"][key] = value

                try:
                    with open(cfg_path, "w", encoding="utf-8") as f:
                        json.dump(existing_data, f, indent=4)
                    _LOG.debug(f"Stored {key}: {value} into {cfg_path}")
                except Exception as e:
                    raise Exception(f"Error while storing {key}: {value} into {cfg_path}") from e

        else:
            raise NameError(f"{key} should not be changed")

    @staticmethod
    def load():
        """Load all variables from the config json file into the runtime storage"""

        cfg_path = Setup._data.cfg_path
        if os.path.isfile(cfg_path):
            try:
                with open(cfg_path, "r", encoding="utf-8") as f:
                    configfile = json.load(f)

                if not isinstance(configfile, dict):
                    raise ValueError("Config file has an invalid structure. Expected a dictionary.")

                if "setup" in configfile:
                    for k, v in configfile["setup"].items():
                        if hasattr(Setup._data, k):
                            setattr(Setup._data, k, v)
                    _LOG.debug(f"Loaded setup data: {configfile['setup']} into runtime storage")
                    if getattr(Setup._data, "setup_complete", False) is False:
                        _LOG.info("First time setup was not completed. Please restart the setup process")
                else:
                    _LOG.warning("No \"setup\" section found in config file. Using default values.")

            except Exception as e:
                raise OSError(f"Error while reading {cfg_path}") from e
        else:
            _LOG.info(f"{cfg_path} does not (yet) exist. Using default setup values.")

class Devices:
    """Class to manage multiple projector devices with all needed configuration data like entity id, ip, password etc.
    
    Includes methods to store them in runtime and saving/loading them from a config file.
    Entity names and IDs are generated at runtime and not persisted to config."""

    __devices = []
    __runtime_entity_data = {}  # Stores generated entity names and IDs at runtime only
    __temp_id = Setup.get(Setup.Keys.SETUP_TEMP_DEVICE_NAME)

    class Keys:
        """Defines all keys that can be set and stored in the device configuration"""
        DEVICE_ID = "device_id"
        IP = "ip"
        NAME = "name"
        ADCP_PASSWORD = "adcp_password"
        ADCP_PORT = "adcp_port"
        ADCP_TIMEOUT = "adcp_timeout"
        SDAP_PORT = "sdap_port"
        MP_POLLER_INTERVAL = "mp_poller_interval"
        HEALTH_POLLER_INTERVAL = "health_poller_interval"


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

        device = next((d for d in Devices.__devices if d.get(DevicesKeys.DEVICE_ID) == device_id), None)
        if device is None:
            raise ValueError(f"Device with device ID \"{device_id}\" does not exist.")

        if key:
            # First check runtime entity data for entity names and IDs
            runtime_key = f"{device_id}#{key}"
            if runtime_key in Devices.__runtime_entity_data:
                return Devices.__runtime_entity_data[runtime_key]

            if key not in device:
                return None
            if key == DevicesKeys.ADCP_PASSWORD:
                salt = PasswordManager.generate_salt()
                try:
                    decrypted_password = PasswordManager.decrypt_password(device[key], salt)
                    return decrypted_password
                except OSError:
                    raise
            return device[key]

        return device

    @staticmethod
    def add(device_id: str = None, entity_data: dict = None, new_device_id: str = None, skip_entity_generation: bool = False):
        """
        Add or update a device. If no device_id is provided, store the data under a temporary ID.
        If a device_id is provided, merge the new data with the existing data.
        Optionally, update the device_id to a new value.

        :param device_id: (Optional) The current ID of the device.
        :param entity_data: A dictionary containing the device configuration data.
        :param new_device_id: (Optional) The new ID to assign to the device.
        :param skip_entity_generation: (Optional) If True, skip automatic entity data generation (used when entity data is already being provided).
        """
        if entity_data is None:
            raise ValueError("entity_data cannot be None")

        if not isinstance(entity_data, dict):
            raise TypeError("entity_data must be a dictionary")

        if device_id is None:
            #If no device_id is provided {Devices.__temp_id} will be used instead
            device_id = Devices.__temp_id

        if DevicesKeys.ADCP_PASSWORD in entity_data:
            salt = PasswordManager.generate_salt()
            encrypted_password = PasswordManager.encrypt_password(entity_data[DevicesKeys.ADCP_PASSWORD], salt)
            entity_data[DevicesKeys.ADCP_PASSWORD] = encrypted_password
            _LOG.debug("Encrypted ADCP password before storing it in the device data")

        # Extract and store entity data in runtime storage (don't keep in entity_data)
        entity_data_copy = entity_data.copy()
        runtime_keys = [k for k in entity_data_copy.keys() if "-id" in k or "-name" in k]

        for key in runtime_keys:
            runtime_key = f"{device_id}#{key}"
            Devices.__runtime_entity_data[runtime_key] = entity_data_copy.pop(key)

        existing_device = next((d for d in Devices.__devices if d.get(DevicesKeys.DEVICE_ID) == device_id), None)

        if existing_device:
            _LOG.debug(f"Adding entity_data {entity_data_copy} to \"{device_id}\"")
            existing_device.update(entity_data_copy)
        else:
            _LOG.debug(f"Adding new device with ID \"{device_id}\"")
            entity_data_copy[DevicesKeys.DEVICE_ID] = device_id
            _LOG.debug(f"Adding entity_data: {entity_data_copy}")
            Devices.__devices.append(entity_data_copy)

        if new_device_id:
            if any(d.get(DevicesKeys.DEVICE_ID) == new_device_id for d in Devices.__devices):
                raise ValueError(f"Device with ID \"{new_device_id}\" already exists")
            _LOG.debug(f"Updating device ID from \"{device_id}\" to \"{new_device_id}\"")
            existing_device[DevicesKeys.DEVICE_ID] = new_device_id

            # Update runtime entity data with new device ID
            old_runtime_keys = [k for k in Devices.__runtime_entity_data.keys() if k.startswith(f"{device_id}#")]
            for old_key in old_runtime_keys:
                new_key = old_key.replace(f"{device_id}#", f"{new_device_id}#", 1)
                Devices.__runtime_entity_data[new_key] = Devices.__runtime_entity_data.pop(old_key)

            # Regenerate entity data with new device ID
            Devices._generate_entity_data(new_device_id)
            Devices._save()
        else:
            # Generate entity data immediately for new or updated devices (unless explicitly skipped)
            if not skip_entity_generation:
                Devices._generate_entity_data(device_id)
            Devices._save()

    @staticmethod
    def remove(device_id: str, key: str = None):
        """
        Remove a device or a specific key from a device by its media player/remote entity ID.
        Saves changes to the config file.
        :param device_id: The entity ID of the device's media player/remote entity.
        :param key: (Optional) The specific key to remove from the device's data.
        """

        device = next((d for d in Devices.__devices if d.get(DevicesKeys.DEVICE_ID) == device_id), None)
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

            # Clean up runtime entity data for removed device
            keys_to_remove = [k for k in Devices.__runtime_entity_data.keys() if k.startswith(f"{device_id}#")]
            for key in keys_to_remove:
                del Devices.__runtime_entity_data[key]
            _LOG.debug(f"Cleaned up runtime entity data for device {device_id}")

        Devices._save()

    @staticmethod
    def list() -> list:
        """
        List all device IDs.
        
        :return: A list of device IDs.
        """
        return [device[DevicesKeys.DEVICE_ID] for device in Devices.__devices]

    @staticmethod
    def extract_device_id_from_entity_id(entity_id: str) -> str | None:
        """
        Extract device_id from an entity_id. Entity IDs follow patterns like:
        - remote-{device_id}
        - sensor-{sensor_type}-{device_id}
        - select-{select_type}-{device_id}
        
        :param entity_id: The entity ID to extract device_id from.
        :return: The device_id if found and valid, None otherwise.
        """
        if not isinstance(entity_id, str):
            return None

        # List of all known device IDs for validation
        known_device_ids = Devices.list()

        # Try to extract device_id by checking if any known device_id is a suffix of the entity_id
        for device_id in known_device_ids:
            if entity_id.endswith(f"-{device_id}"):
                # Verify it matches one of the known patterns
                # Remote pattern: remote-{device_id}
                if entity_id == f"remote-{device_id}":
                    return device_id
                # Sensor pattern: sensor-{type}-{device_id}
                if entity_id.startswith("sensor-") and entity_id.count("-") >= 2:
                    return device_id
                # Select pattern: select-{type}-{device_id}
                if entity_id.startswith("select-") and entity_id.count("-") >= 2:
                    return device_id

        return None

    @staticmethod
    def _save():
        """
        Save all devices to the config file. Already included in add_entity and remove_entity.
        """
        try:
            cfg_path = Setup.get(Setup.Keys.CFG_PATH)
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
        Regenerate entity names and IDs at runtime.
        """
        cfg_path = Setup.get(Setup.Keys.CFG_PATH)
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

                # Clean up any old entity data from runtime storage
                Devices.__runtime_entity_data = {}

                # Generate entity data for all loaded devices
                for device in Devices.__devices:
                    device_id = device.get(DevicesKeys.DEVICE_ID)
                    if device_id:
                        Devices._generate_entity_data(device_id)

                if count < 1:
                    _LOG.debug(f"No devices found in {cfg_path}. Please start the driver setup process")
                else:
                    _LOG.debug(f"Loaded {count} device(s) into runtime storage and regenerated entity data")
            except Exception as e:
                _LOG.error(f"Failed to load device data from {cfg_path}: {e}")
                Devices.__devices = []
                Devices.__runtime_entity_data = {}
        else:
            _LOG.info(f"{cfg_path} does not (yet) exist. No devices loaded. Please start the driver setup process")
            Devices.__devices = []
            Devices.__runtime_entity_data = {}

    @staticmethod #TODO Localize entity names
    def _generate_entity_data(device_id: str):
        """
        Generate entity IDs and names for all entities of a device and store them in runtime storage.
        This is called automatically when loading devices and should not be called manually.
        Only generates data if the device name is available.
        
        :param device_id: The device ID to generate entity data for.
        """
        device = next((d for d in Devices.__devices if d.get(DevicesKeys.DEVICE_ID) == device_id), None)
        if device is None:
            _LOG.warning(f"Cannot generate entity data for device {device_id}: device not found")
            return

        name = device.get(DevicesKeys.NAME)
        if not name:
            _LOG.debug(f"Skipping entity data generation for device {device_id}: device name not yet available")
            return

        sensor_types = SensorTypes.get_all()
        select_types = SelectTypes.get_all()

        # Generate remote entity data
        remote_entity_id = "remote-" + device_id
        remote_entity_name = {
            "en": name + " Remote",
            "de": name + " Remote",
        }

        # Generate sensor entity data
        sensor_light_entity_id = "sensor-light-" + device_id
        sensor_light_entity_name = {
            "en": "Light source timer " + name,
            "de": "Lichtquellen-Timer " + name
        }

        sensor_video_entity_id = "sensor-video-" + device_id
        sensor_video_entity_name = {
            "en": "Video signal " + name,
            "de": "Video-Signal " + name
        }

        sensor_temp_entity_id = "sensor-temp-" + device_id
        sensor_temp_entity_name = {
            "en": "Temperature " + name,
            "de": "Temperatur " + name
        }

        sensor_system_entity_id = "sensor-system-" + device_id
        sensor_system_entity_name = {
            "en": "System status " + name,
            "de": "System-Status " + name
        }

        # Store generated data in runtime
        Devices.__runtime_entity_data.update({
            f"{device_id}#remote-id": remote_entity_id,
            f"{device_id}#remote-name": remote_entity_name,
            f"{device_id}#sensor-light-id": sensor_light_entity_id,
            f"{device_id}#sensor-light-name": sensor_light_entity_name,
            f"{device_id}#sensor-video-id": sensor_video_entity_id,
            f"{device_id}#sensor-video-name": sensor_video_entity_name,
            f"{device_id}#sensor-temp-id": sensor_temp_entity_id,
            f"{device_id}#sensor-temp-name": sensor_temp_entity_name,
            f"{device_id}#sensor-system-id": sensor_system_entity_id,
            f"{device_id}#sensor-system-name": sensor_system_entity_name,
        })

        # Generate additional sensor entity data
        for sensor in sensor_types:
            if sensor not in (SensorTypes.TEMPERATURE, SensorTypes.LIGHT_TIMER, SensorTypes.VIDEO_SIGNAL, SensorTypes.SYSTEM_STATUS):
                if sensor == SensorTypes.CONTRAST_ENHANCER:
                    sensor_name = "Contrast/Dynamic HDR Enhancer"
                else:
                    sensor_name = sensor.replace("-", " ").title().replace("Hdr", "HDR").replace("2d/3d", "2D/3D").replace("3d", "3D")
                Devices.__runtime_entity_data[f"{device_id}#sensor-{sensor}-id"] = f"sensor-{sensor}-{device_id}"
                Devices.__runtime_entity_data[f"{device_id}#sensor-{sensor}-name"] = f"{sensor_name} {name}"

        # Generate select entity data
        for select in select_types:
            if select == SensorTypes.CONTRAST_ENHANCER:
                select_name = "Contrast/Dynamic HDR Enhancer"
            else:
                select_name = select.replace("-", " ").title().replace("Hdr", "HDR").replace("2d/3d", "2D/3D").replace("3d", "3D")
            Devices.__runtime_entity_data[f"{device_id}#select-{select}-id"] = f"select-{select}-{device_id}"
            Devices.__runtime_entity_data[f"{device_id}#select-{select}-name"] = f"{select_name} {name}"

        _LOG.debug(f"Generated entity data for device {device_id}")

    @staticmethod
    def set_entity_name_data(device_id: str):
        """
        Generate entity IDs and names for a device and store them in runtime storage.
        This method is called after the device name has been set.
        
        :param device_id: The device ID to generate entity data for.
        """
        _LOG.info("Generate entity ids and names")
        try:
            Devices._generate_entity_data(device_id)
        except ValueError as v:
            raise ValueError(v) from v

Keys = Setup.Keys
DevicesKeys = Devices.Keys



_SPECIAL_CASES = {
    "1.85_1": "1.85:1",
    "2.35_1": "2.35:1",
    "sim3d": "Simulated 3D",
    "sidebyside": "Side by Side",
    "overunder": "Over Under",
    "v_stretch": "V-Stretch",
    "ycbcr420": "YCbCr 4:2:0",
    "ycbcr422": "YCbCr 4:2:2",
    "ycbcr444": "YCbCr 4:4:4",
    "warn_light_src_life": "Light-Source Error",
    "warn_highland": "High Altitude Warning",
    "warn_temp": "Temperature Warning",
    "warn_signal_freq": "Signal Frequency Warning",
    "warn_signal_sel": "Signal Selection Warning",
    "err_power": "Main Power Supply Error",
    "err_power2": "DC Power Supply or NAND Error",
    "err_system3": "System Error 3 (MAIN_STARTUP)",
    "err_system4": "System Error 4 (WDT)",
    "err_system5": "System Error 5 (BE_STARTUP)",
    "err_cover": "Cover Error",
    "err_light_src": "Light-source Error",
    "err_lens_cover": "Top Cover Or Lens Shutter Error",
    "err_shock": "Drop Shock Error",
    "err_nolens": "Lens Not Attached Error",
    "err_attitude": "Installation Angle Error",
    "err_temp": "Temperature Error",
    "err_fan": "Fan Error",
    "err_wheel": "Wheel Error",
    "err_light_over": "Luminance Error",
    "err_assy": "ASSY Error",
    "err_ballast_update": "Ballast Updating Error"
}

_REVERSE_SPECIAL_CASES = {v: k for k, v in _SPECIAL_CASES.items()}

def convert_options(option: str | list[str], reverse: bool = False) -> str | list[str]:
    """Prettify or reconvert sensor value attributes and select option attributes back to raw ADCP command values. Works with single strings and lists"""

    if isinstance(option, list):
        return [convert_options(item, reverse=reverse) for item in option]

    if not reverse:
        #ADCP values -> Select options/sensor values
        if option in _SPECIAL_CASES:
            return _SPECIAL_CASES[option]

        # Then check for partial matches and replace them
        result = option
        for key, value in _SPECIAL_CASES.items():
            result = result.replace(key, value)

        def _is_numeric(val) -> bool:
            if isinstance(val, (int, float)):
                return True
            if isinstance(val, str):
                try:
                    float(val)
                    return True
                except ValueError:
                    return False
            return False

        if option == result and not _is_numeric(option):
            pretty = option.replace("_", " ").replace("/", " / ").replace("brt", "bright").replace("warn", "warning").replace("err", "error").title()
            #Capitalize common abbreviations
            pretty = pretty.replace("Hdmi", "HDMI").replace("Tv", "TV")\
            .replace("Hdr", "HDR").replace("Sdr", "SDR").replace("Hlg", "HLG")\
            .replace("Bt", "BT.").replace("Rgb", "RGB").replace("Dci", "DCI")
            #Add space before the last digit for options with a single digit at the end
            if len(pretty) >= 2 and pretty[-1].isdigit() and not pretty[-2].isdigit():
                pretty = pretty[:-1] + " " + pretty[-1]
            return pretty

        return result

    # Select/sensor options -> ADCP values
    if option in _REVERSE_SPECIAL_CASES:
        return f"\"{_REVERSE_SPECIAL_CASES[option]}\""

    raw = option.lower().replace(" ", "_").replace("bright", "brt").replace("bt", "bt.").replace("HDMI ", "hdmi")

    if len(raw) >= 3 and raw[-2] == "_" and raw[-1].isdigit():
        raw = raw[:-2] + raw[-1]

    raw = f"\"{raw}\""

    return raw
