#!/usr/bin/env python3

"""Module that includes functions to add a remote entity with all available commands from the media player entity"""

import asyncio
import logging
from typing import Any
import time

import ucapi
import ucapi.ui

import driver
import config
import projector

_LOG = logging.getLogger(__name__)



async def add_remote(device_id: str):
    """Function to add a remote entity"""

    rt_name = config.Devices.get(device_id=device_id, key="remote-name")
    rt_id = config.Devices.get(device_id=device_id, key="remote-id")

    definition = config.Remote().get_def(ent_id=rt_id, name=rt_name)

    driver.api.available_entities.add(definition)

    _LOG.info(f"Added projector remote entity with id {rt_id} and name {rt_name} as available entity")



async def remove_remote(device_id: str):
    """Function to remove a remote entity"""

    rt_name = config.Devices.get(device_id=device_id, key="remote-name")
    rt_id = config.Devices.get(device_id=device_id, key="remote-id")

    definition = config.Remote().get_def(ent_id=rt_id, name=rt_name)

    driver.api.available_entities.add(definition)

    _LOG.info(f"Removed projector remote entity with id {rt_id} and name {rt_name} as available entity")



async def update_rt(device_id: str):
    """Retrieve input source, power status and muted status from the projector, compare them with the known status on the remote and update them if necessary"""

    try:
        power = await projector.get_attr_power(device_id)
    except Exception as e:
        _LOG.error(e)
        _LOG.warning("Can't get power status from projector. Set to Unavailable")
        power = {ucapi.remote.Attributes.STATE: ucapi.remote.States.UNAVAILABLE}

    try:
        api_update_attributes = driver.api.configured_entities.update_attributes(device_id, power)
        if not api_update_attributes:
            driver.api.available_entities.update_attributes(device_id, power)
    except Exception as e:
        raise Exception("Error while updating status attribute for entity id " + device_id) from e

    _LOG.info("Updated remote entity status attribute to " + str(power) + " for " + device_id)



async def remote_cmd_handler(
    entity: ucapi.Remote, cmd_id: str, params: dict[str, Any] | None
) -> ucapi.StatusCodes:
    """
    Remote command handler.

    Called by the integration-API if a command is sent to a configured remote-entity.

    :param entity: remote entity
    :param cmd_id: command
    :param params: optional command parameters
    :return: status of the command
    """

    device_id = entity.id.replace("remote-","")

    if not params:
        _LOG.info(f"Received {cmd_id} command for {entity.id}")
    else:
        _LOG.info(f"Received {cmd_id} command with parameter {params} for {entity.id}")
        repeat = params.get("repeat")
        delay = params.get("delay")
        hold = params.get("hold")

        if hold is None or hold == "":
            hold = 0
        if repeat is None:
            repeat = 1
        if delay is None:
            delay = 0
        else:
            delay = delay / 1000 #Convert milliseconds to seconds for sleep

        if repeat == 1 and delay != 0:
            _LOG.debug(str(delay) + " seconds delay will be ignored as the command will not be repeated (repeat = 1)")
            delay = 0

    def rep_warn():
        if repeat != 1:
            _LOG.warning("Execution of the command " + command + " failed. Remaining " + str(repeat-1) + " repetitions will no longer be executed")

    match cmd_id:

        case \
            ucapi.remote.Commands.ON | \
            ucapi.remote.Commands.OFF | \
            ucapi.remote.Commands.TOGGLE:
            try:
                await projector.send_cmd(device_id, cmd_id)
            except TimeoutError:
                return ucapi.StatusCodes.TIMEOUT
            except PermissionError:
                return ucapi.StatusCodes.UNAUTHORIZED
            except KeyError:
                return ucapi.StatusCodes.NOT_IMPLEMENTED
            except (ConnectionError, ConnectionRefusedError, ConnectionResetError):
                return ucapi.StatusCodes.SERVER_ERROR
            except Exception as e:
                error = str(e)
                if error is not None:
                    _LOG.error(f"Failed to send command {cmd_id}: {error}")
                return ucapi.StatusCodes.BAD_REQUEST
            return ucapi.StatusCodes.OK

        case \
            ucapi.remote.Commands.SEND_CMD:

            command = params.get("command")

            try:
                i = 0
                r = range(repeat)
                for i in r:
                    i = i+1
                    if repeat != 1:
                        _LOG.debug("Round " + str(i) + " for command " + command)
                    if hold != 0:
                        cmd_start = time.time()*1000
                        while time.time()*1000 - cmd_start < hold:
                            await projector.send_cmd(device_id, command)
                            await asyncio.sleep(0)
                    else:
                        await projector.send_cmd(device_id, command)
                        await asyncio.sleep(0)
                    await asyncio.sleep(delay)
            except TimeoutError:
                rep_warn()
                return ucapi.StatusCodes.TIMEOUT
            except PermissionError:
                rep_warn()
                return ucapi.StatusCodes.UNAUTHORIZED
            except KeyError:
                rep_warn()
                return ucapi.StatusCodes.NOT_IMPLEMENTED
            except (ConnectionError, ConnectionRefusedError, ConnectionResetError):
                rep_warn()
                return ucapi.StatusCodes.SERVER_ERROR
            except Exception as e:
                rep_warn()
                error = str(e)
                if error:
                    _LOG.error(f"Failed to send command {command}: {error}")
                return ucapi.StatusCodes.BAD_REQUEST

            return ucapi.StatusCodes.OK

        case \
            ucapi.remote.Commands.SEND_CMD_SEQUENCE:

            sequence = params.get("sequence")

            _LOG.info(f"Command sequence: {sequence}")

            for command in sequence:
                _LOG.debug("Sending command: " + command)
                try:
                    i = 0
                    r = range(repeat)
                    for i in r:
                        i = i+1
                        if repeat != 1:
                            _LOG.debug("Round " + str(i) + " for command " + command)
                        if hold != 0:
                            cmd_start = time.time()*1000
                            while time.time()*1000 - cmd_start < hold:
                                await projector.send_cmd(device_id, command)
                                await asyncio.sleep(0)
                        else:
                            await projector.send_cmd(device_id, command)
                            await asyncio.sleep(0)
                        await asyncio.sleep(delay)
                except TimeoutError:
                    rep_warn()
                    return ucapi.StatusCodes.TIMEOUT
                except PermissionError:
                    rep_warn()
                    return ucapi.StatusCodes.UNAUTHORIZED
                except KeyError:
                    rep_warn()
                    return ucapi.StatusCodes.NOT_IMPLEMENTED
                except (ConnectionError, ConnectionRefusedError, ConnectionResetError):
                    rep_warn()
                    return ucapi.StatusCodes.SERVER_ERROR
                except Exception as e:
                    rep_warn()
                    error = str(e)
                    if error:
                        _LOG.error(f"Failed to send command {command}: {error}")
                    return ucapi.StatusCodes.BAD_REQUEST

            return ucapi.StatusCodes.OK

        case _:

            _LOG.info(f"Unsupported command: {cmd_id} for {entity.id}")
            return ucapi.StatusCodes.BAD_REQUEST



def create_button_mappings() -> list[ucapi.ui.DeviceButtonMapping | dict[str, Any]]:
    """Create the button mapping of the remote entity"""
    return [
        ucapi.ui.create_btn_mapping(ucapi.ui.Buttons.BACK, ucapi.media_player.Commands.BACK),
        ucapi.ui.create_btn_mapping(ucapi.ui.Buttons.HOME, ucapi.media_player.Commands.MENU),
        # ucapi.ui.create_btn_mapping(ucapi.ui.Buttons.VOICE, "", "")),
        # ucapi.ui.create_btn_mapping(ucapi.ui.Buttons.VOLUME_UP, "", ""),
        # ucapi.ui.create_btn_mapping(ucapi.ui.Buttons.VOLUME_DOWN, "", ""),
        ucapi.ui.create_btn_mapping(ucapi.ui.Buttons.MUTE, config.SimpleCommands.PICTURE_MUTING_TOGGLE),
        ucapi.ui.create_btn_mapping(ucapi.ui.Buttons.DPAD_UP, ucapi.media_player.Commands.CURSOR_UP),
        ucapi.ui.create_btn_mapping(ucapi.ui.Buttons.DPAD_DOWN, ucapi.media_player.Commands.CURSOR_DOWN),
        ucapi.ui.create_btn_mapping(ucapi.ui.Buttons.DPAD_LEFT, ucapi.media_player.Commands.CURSOR_LEFT),
        ucapi.ui.create_btn_mapping(ucapi.ui.Buttons.DPAD_RIGHT, ucapi.media_player.Commands.CURSOR_RIGHT),
        ucapi.ui.create_btn_mapping(ucapi.ui.Buttons.DPAD_MIDDLE, ucapi.media_player.Commands.CURSOR_ENTER),
        # ucapi.ui.create_btn_mapping(ucapi.ui.Buttons.GREEN, "", ""),
        # ucapi.ui.create_btn_mapping(ucapi.ui.Buttons.YELLOW, "", ""),
        # ucapi.ui.create_btn_mapping(ucapi.ui.Buttons.RED, "", ""),
        # ucapi.ui.create_btn_mapping(ucapi.ui.Buttons.BLUE, "", ""),
        # ucapi.ui.create_btn_mapping(ucapi.ui.Buttons.CHANNEL_DOWN, ""),
        # ucapi.ui.create_btn_mapping(ucapi.ui.Buttons.CHANNEL_UP, ""),
        # ucapi.ui.create_btn_mapping(ucapi.ui.Buttons.PREV, "", ""),
        # ucapi.ui.create_btn_mapping(ucapi.ui.Buttons.PLAY, ""),
        # ucapi.ui.create_btn_mapping(ucapi.ui.Buttons.NEXT, "", ""),
        ucapi.ui.create_btn_mapping(ucapi.ui.Buttons.POWER, ucapi.remote.Commands.TOGGLE),
    ]



def create_ui_pages() -> list[ucapi.ui.UiPage | dict[str, Any]]:
    """Create a user interface with different pages that includes all commands"""

    ui_page1 = ucapi.ui.UiPage("page1", "Power, Inputs & HDR", grid=ucapi.ui.Size(6, 7))
    ui_page1.add(ucapi.ui.create_ui_text("On", 0, 0, size=ucapi.ui.Size(2, 1), cmd=ucapi.remote.Commands.ON))
    ui_page1.add(ucapi.ui.create_ui_text("Off", 2, 0, size=ucapi.ui.Size(2, 1), cmd=ucapi.remote.Commands.OFF))
    ui_page1.add(ucapi.ui.create_ui_icon("uc:info", 4, 0, size=ucapi.ui.Size(2, 1), \
                                        cmd=ucapi.remote.create_sequence_cmd([ucapi.media_player.Commands.MENU,ucapi.media_player.Commands.CURSOR_UP])))
    ui_page1.add(ucapi.ui.create_ui_text("HDMI 1", 0, 1, size=ucapi.ui.Size(3, 1), cmd=ucapi.remote.create_send_cmd(config.SimpleCommands.INPUT_HDMI1)))
    ui_page1.add(ucapi.ui.create_ui_text("HDMI 2", 3, 1, size=ucapi.ui.Size(3, 1), cmd=ucapi.remote.create_send_cmd(config.SimpleCommands.INPUT_HDMI2)))
    ui_page1.add(ucapi.ui.create_ui_text("-- HDR --", 0, 2, size=ucapi.ui.Size(6, 1)))
    ui_page1.add(ucapi.ui.create_ui_text("On", 0, 3, size=ucapi.ui.Size(2, 1), cmd=ucapi.remote.create_send_cmd(config.SimpleCommands.MODE_HDR_ON)))
    ui_page1.add(ucapi.ui.create_ui_text("Off", 2, 3, size=ucapi.ui.Size(2, 1), cmd=ucapi.remote.create_send_cmd(config.SimpleCommands.MODE_HDR_OFF)))
    ui_page1.add(ucapi.ui.create_ui_text("Auto", 4, 3, size=ucapi.ui.Size(2, 1), cmd=ucapi.remote.create_send_cmd(config.SimpleCommands.MODE_HDR_AUTO)))
    ui_page1.add(ucapi.ui.create_ui_text("-- HDR Dynamic Tone Mapping --", 0, 4, size=ucapi.ui.Size(6, 1)))
    ui_page1.add(ucapi.ui.create_ui_text("Off", 1, 5, size=ucapi.ui.Size(1, 1), cmd=ucapi.remote.create_send_cmd(config.SimpleCommands.MODE_HDR_DYN_TONE_MAPPING_OFF)))
    ui_page1.add(ucapi.ui.create_ui_text("Mode 1", 2, 5, size=ucapi.ui.Size(1, 1), cmd=ucapi.remote.create_send_cmd(config.SimpleCommands.MODE_HDR_DYN_TONE_MAPPING_1)))
    ui_page1.add(ucapi.ui.create_ui_text("Mode 2", 3, 5, size=ucapi.ui.Size(1, 1), cmd=ucapi.remote.create_send_cmd(config.SimpleCommands.MODE_HDR_DYN_TONE_MAPPING_2)))
    ui_page1.add(ucapi.ui.create_ui_text("Mode 3", 4, 5, size=ucapi.ui.Size(1, 1), cmd=ucapi.remote.create_send_cmd(config.SimpleCommands.MODE_HDR_DYN_TONE_MAPPING_3)))

    ui_page2 = ucapi.ui.UiPage("page2", "Picture Modes")
    ui_page2.add(ucapi.ui.create_ui_text("-- Picture Modes --", 0, 0, size=ucapi.ui.Size(4, 1)))
    ui_page2.add(ucapi.ui.create_ui_text("Cinema Film 1", 0, 1, size=ucapi.ui.Size(2, 1), cmd=ucapi.remote.create_send_cmd(config.SimpleCommands.MODE_PRESET_CINEMA_FILM_1)))
    ui_page2.add(ucapi.ui.create_ui_text("Cinema Film 2", 2, 1, size=ucapi.ui.Size(2, 1), cmd=ucapi.remote.create_send_cmd(config.SimpleCommands.MODE_PRESET_CINEMA_FILM_2)))
    ui_page2.add(ucapi.ui.create_ui_text("Reference", 0, 2, size=ucapi.ui.Size(2, 1), cmd=ucapi.remote.create_send_cmd(config.SimpleCommands.MODE_PRESET_REF)))
    ui_page2.add(ucapi.ui.create_ui_text("Game", 2, 2, size=ucapi.ui.Size(2, 1), cmd=ucapi.remote.create_send_cmd(config.SimpleCommands.MODE_PRESET_GAME)))
    ui_page2.add(ucapi.ui.create_ui_text("TV", 0, 3, size=ucapi.ui.Size(2, 1), cmd=ucapi.remote.create_send_cmd(config.SimpleCommands.MODE_PRESET_TV)))
    ui_page2.add(ucapi.ui.create_ui_text("Bright TV", 2, 3, size=ucapi.ui.Size(2, 1), cmd=ucapi.remote.create_send_cmd(config.SimpleCommands.MODE_PRESET_BRIGHT_TV)))
    ui_page2.add(ucapi.ui.create_ui_text("Bright Cinema", 0, 4, size=ucapi.ui.Size(2, 1), cmd=ucapi.remote.create_send_cmd(config.SimpleCommands.MODE_PRESET_BRIGHT_CINEMA)))
    ui_page2.add(ucapi.ui.create_ui_text("Photo", 2, 4, size=ucapi.ui.Size(2, 1), cmd=ucapi.remote.create_send_cmd(config.SimpleCommands.MODE_PRESET_PHOTO)))
    ui_page2.add(ucapi.ui.create_ui_text("User", 1, 5, size=ucapi.ui.Size(2, 1), cmd=ucapi.remote.create_send_cmd(config.SimpleCommands.MODE_PRESET_USER)))

    ui_page3 = ucapi.ui.UiPage("page3", "Aspect Ratios")
    ui_page3.add(ucapi.ui.create_ui_text("-- Aspect Ratios --", 0, 0, size=ucapi.ui.Size(4, 1)))
    ui_page3.add(ucapi.ui.create_ui_text("Normal", 0, 1, size=ucapi.ui.Size(2, 1), cmd=ucapi.remote.create_send_cmd(config.SimpleCommands.MODE_ASPECT_RATIO_NORMAL)))
    ui_page3.add(ucapi.ui.create_ui_text("Squeeze", 2, 1, size=ucapi.ui.Size(2, 1), cmd=ucapi.remote.create_send_cmd(config.SimpleCommands.MODE_ASPECT_RATIO_SQUEEZE)))
    ui_page3.add(ucapi.ui.create_ui_text("Stretch", 0, 2, size=ucapi.ui.Size(2, 1), cmd=ucapi.remote.create_send_cmd(config.SimpleCommands.MODE_ASPECT_RATIO_STRETCH)))
    ui_page3.add(ucapi.ui.create_ui_text("V Stretch", 2, 2, size=ucapi.ui.Size(2, 1), cmd=ucapi.remote.create_send_cmd(config.SimpleCommands.MODE_ASPECT_RATIO_V_STRETCH)))
    ui_page3.add(ucapi.ui.create_ui_text("Zoom 1:85", 0, 3, size=ucapi.ui.Size(2, 1), cmd=ucapi.remote.create_send_cmd(config.SimpleCommands.MODE_ASPECT_RATIO_ZOOM_1_85)))
    ui_page3.add(ucapi.ui.create_ui_text("Zoom 2:35", 2, 3, size=ucapi.ui.Size(2, 1), cmd=ucapi.remote.create_send_cmd(config.SimpleCommands.MODE_ASPECT_RATIO_ZOOM_2_35)))

    ui_page4 = ucapi.ui.UiPage("page4", "Picture Positions Select")
    ui_page4.add(ucapi.ui.create_ui_text("-- Picture Positions Select --", 0, 0, size=ucapi.ui.Size(4, 1)))
    ui_page4.add(ucapi.ui.create_ui_text("1,85", 0, 1, size=ucapi.ui.Size(2, 1), cmd=ucapi.remote.create_send_cmd(config.SimpleCommands.PICTURE_POSITION_SELECT_1_85)))
    ui_page4.add(ucapi.ui.create_ui_text("2,35", 2, 1, size=ucapi.ui.Size(2, 1), cmd=ucapi.remote.create_send_cmd(config.SimpleCommands.PICTURE_POSITION_SELECT_2_35)))
    ui_page4.add(ucapi.ui.create_ui_text("Custom 1", 0, 2, size=ucapi.ui.Size(2, 1), cmd=ucapi.remote.create_send_cmd(config.SimpleCommands.PICTURE_POSITION_SELECT_CUSTOM_1)))
    ui_page4.add(ucapi.ui.create_ui_text("Custom 2", 2, 2, size=ucapi.ui.Size(2, 1), cmd=ucapi.remote.create_send_cmd(config.SimpleCommands.PICTURE_POSITION_SELECT_CUSTOM_2)))
    ui_page4.add(ucapi.ui.create_ui_text("Custom 3", 0, 3, size=ucapi.ui.Size(2, 1), cmd=ucapi.remote.create_send_cmd(config.SimpleCommands.PICTURE_POSITION_SELECT_CUSTOM_3)))
    ui_page4.add(ucapi.ui.create_ui_text("Custom 4", 2, 3, size=ucapi.ui.Size(2, 1), cmd=ucapi.remote.create_send_cmd(config.SimpleCommands.PICTURE_POSITION_SELECT_CUSTOM_4)))
    ui_page4.add(ucapi.ui.create_ui_text("Custom 5", 1, 4, size=ucapi.ui.Size(2, 1), cmd=ucapi.remote.create_send_cmd(config.SimpleCommands.PICTURE_POSITION_SELECT_CUSTOM_5)))

    ui_page5 = ucapi.ui.UiPage("page5", "Picture Positions Save")
    ui_page5.add(ucapi.ui.create_ui_text("-- Picture Positions Save --", 0, 0, size=ucapi.ui.Size(4, 1)))
    ui_page5.add(ucapi.ui.create_ui_text("1,85", 0, 1, size=ucapi.ui.Size(2, 1), cmd=ucapi.remote.create_send_cmd(config.SimpleCommands.PICTURE_POSITION_SAVE_1_85)))
    ui_page5.add(ucapi.ui.create_ui_text("2,35", 2, 1, size=ucapi.ui.Size(2, 1), cmd=ucapi.remote.create_send_cmd(config.SimpleCommands.PICTURE_POSITION_SAVE_2_35)))
    ui_page5.add(ucapi.ui.create_ui_text("Custom 1", 0, 2, size=ucapi.ui.Size(2, 1), cmd=ucapi.remote.create_send_cmd(config.SimpleCommands.PICTURE_POSITION_SAVE_CUSTOM_1)))
    ui_page5.add(ucapi.ui.create_ui_text("Custom 2", 2, 2, size=ucapi.ui.Size(2, 1), cmd=ucapi.remote.create_send_cmd(config.SimpleCommands.PICTURE_POSITION_SAVE_CUSTOM_2)))
    ui_page5.add(ucapi.ui.create_ui_text("Custom 3", 0, 3, size=ucapi.ui.Size(2, 1), cmd=ucapi.remote.create_send_cmd(config.SimpleCommands.PICTURE_POSITION_SAVE_CUSTOM_3)))
    ui_page5.add(ucapi.ui.create_ui_text("Custom 4", 2, 3, size=ucapi.ui.Size(2, 1), cmd=ucapi.remote.create_send_cmd(config.SimpleCommands.PICTURE_POSITION_SAVE_CUSTOM_4)))
    ui_page5.add(ucapi.ui.create_ui_text("Custom 5", 1, 4, size=ucapi.ui.Size(2, 1), cmd=ucapi.remote.create_send_cmd(config.SimpleCommands.PICTURE_POSITION_SAVE_CUSTOM_5)))

    ui_page6 = ucapi.ui.UiPage("page6", "Motionflow")
    ui_page6.add(ucapi.ui.create_ui_text("-- Motionflow --", 0, 0, size=ucapi.ui.Size(4, 1)))
    ui_page6.add(ucapi.ui.create_ui_text("Off", 0, 1, size=ucapi.ui.Size(2, 1), cmd=ucapi.remote.create_send_cmd(config.SimpleCommands.MODE_MOTIONFLOW_OFF)))
    ui_page6.add(ucapi.ui.create_ui_text("True Cinema", 2, 1, size=ucapi.ui.Size(2, 1), cmd=ucapi.remote.create_send_cmd(config.SimpleCommands.MODE_MOTIONFLOW_TRUE_CINEMA)))
    ui_page6.add(ucapi.ui.create_ui_text("Smooth High", 0, 2, size=ucapi.ui.Size(2, 1), cmd=ucapi.remote.create_send_cmd(config.SimpleCommands.MODE_MOTIONFLOW_SMOOTH_HIGH)))
    ui_page6.add(ucapi.ui.create_ui_text("Smooth Low", 2, 2, size=ucapi.ui.Size(2, 1), cmd=ucapi.remote.create_send_cmd(config.SimpleCommands.MODE_MOTIONFLOW_SMOOTH_LOW)))
    ui_page6.add(ucapi.ui.create_ui_text("Impulse", 0, 3, size=ucapi.ui.Size(2, 1), cmd=ucapi.remote.create_send_cmd(config.SimpleCommands.MODE_MOTIONFLOW_IMPULSE)))
    ui_page6.add(ucapi.ui.create_ui_text("Combination", 2, 3, size=ucapi.ui.Size(2, 1), cmd=ucapi.remote.create_send_cmd(config.SimpleCommands.MODE_MOTIONFLOW_COMBINATION)))

    ui_page7 = ucapi.ui.UiPage("page7", "2D / 3D", grid=ucapi.ui.Size(6, 6))
    ui_page7.add(ucapi.ui.create_ui_text("-- 2D/3D Display Select --", 0, 0, size=ucapi.ui.Size(6, 1)))
    ui_page7.add(ucapi.ui.create_ui_text("2D", 0, 1, size=ucapi.ui.Size(2, 1), cmd=ucapi.remote.create_send_cmd(config.SimpleCommands.MODE_2D_3D_SELECT_2D)))
    ui_page7.add(ucapi.ui.create_ui_text("3D", 2, 1, size=ucapi.ui.Size(2, 1), cmd=ucapi.remote.create_send_cmd(config.SimpleCommands.MODE_2D_3D_SELECT_3D)))
    ui_page7.add(ucapi.ui.create_ui_text("Auto", 4, 1, size=ucapi.ui.Size(2, 1), cmd=ucapi.remote.create_send_cmd(config.SimpleCommands.MODE_2D_3D_SELECT_AUTO)))
    ui_page7.add(ucapi.ui.create_ui_text("-- 3D Format --", 0, 2, size=ucapi.ui.Size(6, 1)))
    ui_page7.add(ucapi.ui.create_ui_text("Simulated 3D", 0, 3, size=ucapi.ui.Size(2, 1), cmd=ucapi.remote.create_send_cmd(config.SimpleCommands.MODE_3D_FORMAT_SIMULATED_3D)))
    ui_page7.add(ucapi.ui.create_ui_text("Side-by-Side", 2, 3, size=ucapi.ui.Size(2, 1), cmd=ucapi.remote.create_send_cmd(config.SimpleCommands.MODE_3D_FORMAT_SIDE_BY_SIDE)))
    ui_page7.add(ucapi.ui.create_ui_text("Over-Under", 4, 3, size=ucapi.ui.Size(2, 1), cmd=ucapi.remote.create_send_cmd(config.SimpleCommands.MODE_3D_FORMAT_OVER_UNDER)))

    ui_page8 = ucapi.ui.UiPage("page8", "Lens Control", grid=ucapi.ui.Size(4, 7))
    ui_page8.add(ucapi.ui.create_ui_text("-- Lens Control --", 0, 0, size=ucapi.ui.Size(4, 1)))
    ui_page8.add(ucapi.ui.create_ui_text("-- Focus --", 0, 1, size=ucapi.ui.Size(2, 1)))
    ui_page8.add(ucapi.ui.create_ui_text("-- Zoom --", 2, 1, size=ucapi.ui.Size(2, 1)))
    ui_page8.add(ucapi.ui.create_ui_icon("uc:up-arrow", 0, 2, size=ucapi.ui.Size(2, 1), cmd=ucapi.remote.create_send_cmd(config.SimpleCommands.LENS_FOCUS_NEAR)))
    ui_page8.add(ucapi.ui.create_ui_icon("uc:down-arrow", 0, 3, size=ucapi.ui.Size(2, 1), cmd=ucapi.remote.create_send_cmd(config.SimpleCommands.LENS_FOCUS_FAR)))
    ui_page8.add(ucapi.ui.create_ui_icon("uc:up-arrow-bold", 2, 2, size=ucapi.ui.Size(2, 1), cmd=ucapi.remote.create_send_cmd(config.SimpleCommands.LENS_ZOOM_LARGE)))
    ui_page8.add(ucapi.ui.create_ui_icon("uc:down-arrow-bold", 2, 3, size=ucapi.ui.Size(2, 1), cmd=ucapi.remote.create_send_cmd(config.SimpleCommands.LENS_ZOOM_SMALL)))
    ui_page8.add(ucapi.ui.create_ui_icon("uc:up-arrow-alt", 1, 4, size=ucapi.ui.Size(2, 1), cmd=ucapi.remote.create_send_cmd(config.SimpleCommands.LENS_SHIFT_UP)))
    ui_page8.add(ucapi.ui.create_ui_icon("uc:left-arrow-alt", 0, 5, size=ucapi.ui.Size(2, 1), cmd=ucapi.remote.create_send_cmd(config.SimpleCommands.LENS_SHIFT_LEFT)))
    ui_page8.add(ucapi.ui.create_ui_icon("uc:right-arrow-alt", 2, 5, size=ucapi.ui.Size(2, 1), cmd=ucapi.remote.create_send_cmd(config.SimpleCommands.LENS_SHIFT_RIGHT)))
    ui_page8.add(ucapi.ui.create_ui_icon("uc:down-arrow-alt", 1, 6, size=ucapi.ui.Size(2, 1), cmd=ucapi.remote.create_send_cmd(config.SimpleCommands.LENS_SHIFT_DOWN)))

    ui_page9 = ucapi.ui.UiPage("page9", "Lamp Control", grid=ucapi.ui.Size(6, 8))
    ui_page9.add(ucapi.ui.create_ui_text("-- Lamp Control --", 0, 0, size=ucapi.ui.Size(3, 1)))
    ui_page9.add(ucapi.ui.create_ui_text("-- Laser Dimming --", 3, 0, size=ucapi.ui.Size(3, 1)))
    ui_page9.add(ucapi.ui.create_ui_text("High", 0, 1, size=ucapi.ui.Size(3, 1), cmd=ucapi.remote.create_send_cmd(config.SimpleCommands.LAMP_CONTROL_HIGH)))
    ui_page9.add(ucapi.ui.create_ui_text("Low", 0, 2, size=ucapi.ui.Size(3, 1), cmd=ucapi.remote.create_send_cmd(config.SimpleCommands.LAMP_CONTROL_LOW)))
    ui_page9.add(ucapi.ui.create_ui_icon("uc:up-arrow", 3, 1, size=ucapi.ui.Size(3, 1), cmd=ucapi.remote.create_send_cmd(config.SimpleCommands.LASER_DIM_UP)))
    ui_page9.add(ucapi.ui.create_ui_icon("uc:down-arrow", 3, 2, size=ucapi.ui.Size(3, 1), cmd=ucapi.remote.create_send_cmd(config.SimpleCommands.LASER_DIM_DOWN)))
    ui_page9.add(ucapi.ui.create_ui_text("-- Iris Dynamic Control --", 0, 3, size=ucapi.ui.Size(3, 1)))
    ui_page9.add(ucapi.ui.create_ui_text("-- Light Source Dynamic Control --", 3, 3, size=ucapi.ui.Size(3, 1)))
    ui_page9.add(ucapi.ui.create_ui_text("Off", 0, 4, size=ucapi.ui.Size(3, 1), cmd=ucapi.remote.create_send_cmd(config.SimpleCommands.MODE_DYN_IRIS_CONTROL_OFF)))
    ui_page9.add(ucapi.ui.create_ui_text("Full", 0, 5, size=ucapi.ui.Size(3, 1), cmd=ucapi.remote.create_send_cmd(config.SimpleCommands.MODE_DYN_IRIS_CONTROL_FULL)))
    ui_page9.add(ucapi.ui.create_ui_text("Limited", 0, 6, size=ucapi.ui.Size(3, 1), cmd=ucapi.remote.create_send_cmd(config.SimpleCommands.MODE_DYN_IRIS_CONTROL_LIMITED)))
    ui_page9.add(ucapi.ui.create_ui_text("Off", 3, 4, size=ucapi.ui.Size(3, 1), cmd=ucapi.remote.create_send_cmd(config.SimpleCommands.MODE_DYN_LIGHT_CONTROL_OFF)))
    ui_page9.add(ucapi.ui.create_ui_text("Full", 3, 5, size=ucapi.ui.Size(3, 1), cmd=ucapi.remote.create_send_cmd(config.SimpleCommands.MODE_DYN_LIGHT_CONTROL_FULL)))
    ui_page9.add(ucapi.ui.create_ui_text("Limited", 3, 6, size=ucapi.ui.Size(3, 1), cmd=ucapi.remote.create_send_cmd(config.SimpleCommands.MODE_DYN_LIGHT_CONTROL_LIMITED)))

    ui_page10 = ucapi.ui.UiPage("page10", "Miscellaneous")
    ui_page10.add(ucapi.ui.create_ui_text("-- Input Lag Reduction --", 0, 0, size=ucapi.ui.Size(4, 1)))
    ui_page10.add(ucapi.ui.create_ui_text("On", 0, 1, size=ucapi.ui.Size(2, 1), cmd=ucapi.remote.create_send_cmd(config.SimpleCommands.INPUT_LAG_REDUCTION_ON)))
    ui_page10.add(ucapi.ui.create_ui_text("Off", 2, 1, size=ucapi.ui.Size(2, 1), cmd=ucapi.remote.create_send_cmd(config.SimpleCommands.INPUT_LAG_REDUCTION_OFF)))
    ui_page10.add(ucapi.ui.create_ui_text("-- Menu Position --", 0, 2, size=ucapi.ui.Size(4, 1)))
    ui_page10.add(ucapi.ui.create_ui_text("Bottom Left", 0, 3, size=ucapi.ui.Size(2, 1), cmd=ucapi.remote.create_send_cmd(config.SimpleCommands.MENU_POSITION_BOTTOM_LEFT)))
    ui_page10.add(ucapi.ui.create_ui_text("Center", 2, 3, size=ucapi.ui.Size(2, 1), cmd=ucapi.remote.create_send_cmd(config.SimpleCommands.MENU_POSITION_CENTER)))

    return [ui_page1, ui_page2, ui_page3, ui_page4, ui_page5, ui_page6, ui_page7, ui_page8, ui_page9, ui_page10]
