#!/usr/bin/env python3

"""Module that includes functions to execute ADCP and SDAP commands"""

import logging
import json
import re

import ucapi

import config
import driver
import sensor
import media_player
import adcp as ADCP

_LOG = logging.getLogger(__name__)



def projector_def(device_id:str = None):
    """Create the projector object. Use custom ports and password if they differ from the projectors default values
    
    :device_id: The id of the device in config.Devices. If empty the temp device id from config.Setup will be used e.g. during setup
    """

    if device_id is None:
        #Using temp device id for projector object definition during setup
        device_id = config.Setup.get("setup_temp_device")

    ip = config.Devices.get(device_id=device_id, key="ip")
    adcp_password = config.Devices.get(device_id=device_id, key="adcp_password")
    adcp_port = config.Devices.get(device_id=device_id, key="adcp_port")
    adcp_timeout = config.Devices.get(device_id=device_id, key="adcp_timeout")
    sdap_port = config.Devices.get(device_id=device_id, key="sdap_port")

    attr = {"ip": ip, "adcp_port": adcp_port, "sdap_port": sdap_port, "adcp_password": adcp_password, "adcp_timeout": adcp_timeout}

    # Only include attributes that are not None (non default values) when creating the projector object
    valid_attributes = {key: value for key, value in attr.items() if value is not None}

    return ADCP.Projector(**valid_attributes)



async def get_attr_power(device_id: str):
    """Get the current power status from the projector and return the corresponding ucapi power status attribute"""

    _LOG.debug(f"Get current power status for {device_id}")
    try:
        power_state = await projector_def(device_id).command(ADCP.Get.POWER)
    except Exception as e:
        raise type(e)(str(e)) from e
    if power_state in (ADCP.Values.States.STANDBY, ADCP.Values.States.COOLING1, ADCP.Values.States.COOLING2):
        #TODO Test if UC standby status is really shown in the remote ui and not only part of the ucapi, If so create a separate case
        return {ucapi.media_player.Attributes.STATE: ucapi.media_player.States.OFF} #Can be used for remote entities as well
    if power_state in (ADCP.Values.States.ON, ADCP.Values.States.STARTUP):
        return {ucapi.media_player.Attributes.STATE: ucapi.media_player.States.ON}



async def get_attr_muted(device_id: str):
    """Get the current muted status from the projector and return either False or True"""

    _LOG.debug(f"Get mute state for {device_id}")
    try:
        if await projector_def(device_id).command(ADCP.Get.MUTE) == ADCP.Values.States.ON:
            return True
        return False
    except Exception as e:
        raise type(e)(str(e)) from e



async def get_attr_source(device_id: str):
    """Get the current input source from the projector and return it as a string"""

    _LOG.debug(f"Get current input for {device_id}")
    try:
        if await projector_def(device_id).command(ADCP.Get.INPUT) == ADCP.Values.Inputs.HDMI1:
            return config.Sources.HDMI_1
        return config.Sources.HDMI_2
    except Exception as e:
        raise type(e)(str(e)) from e



async def get_light_source_hours(device_id: str = None):
    """Get the light source hours from the projector"""

    if device_id is None:
        #If no device_id is provided a temp device will be used instead
        device_id = config.Setup.get("setup_temp_device")

    _LOG.debug(f"Get light source hours for {device_id}")

    try:
        response = await projector_def(device_id).command(ADCP.Get.TIMER)
        if response:
            try:
                hours_data = json.loads(response)
                for item in hours_data:
                    if "light_src" in item:
                        return item["light_src"]
                _LOG.warning(f"No light_src data found in response: {response}")
            except json.JSONDecodeError as e:
                _LOG.error(f"Failed to parse timer response: {e}")
                _LOG.debug(f"Raw response: {response}")
        return None
    except Exception as e:
        _LOG.error(e)
        raise type(e) from e



async def get_temp(device_id: str = None):
    """Get the temperature from the projector"""

    _LOG.debug(f"Get temperature for {device_id}")

    try:
        response = await projector_def(device_id).command(ADCP.Get.TEMPERATURE)
        if response:
            try:
                hours_data = json.loads(response)
                for item in hours_data:
                    if "intake_air" in item:
                        return int(item["intake_air"])
                _LOG.warning(f"No intake_air data found in response: {response}")
            except json.JSONDecodeError as e:
                _LOG.error(f"Failed to parse temperature response: {e}")
                _LOG.debug(f"Raw response: {response}")
    except OSError:
        _LOG.info("Temperature polling is temporally unavailable. The projector is probably turned off")
        _LOG.debug("Returning an empty string as value")
        return ""
    except NameError:
        _LOG.info("Temperature polling is not supported on this projector model")
        _LOG.debug("Retuning N/A as value")
        return "N/A"
    except Exception as e:
        _LOG.error(e)
        raise type(e) from e


async def get_error(device_id: str = None):
    """Get error messages from the projector"""

    _LOG.debug(f"Get error messages for {device_id}")

    try:
        response = await projector_def(device_id).command(ADCP.Get.ERROR)
        if response:
            try:
                error_msg_json = json.loads(response)
                if isinstance(error_msg_json, list):
                    error_msgs = [
                        str(item).replace("err", "error").replace("_", " ").title()
                        for item in error_msg_json if item
                    ]
                    if error_msgs:
                        return ", ".join(error_msgs)
                    _LOG.warning(f"No error message data found in response: {response}")
                    return ""
            except json.JSONDecodeError as e:
                _LOG.error(f"Failed to parse error message response: {e}")
                _LOG.debug(f"Raw response: {response}")
    except Exception as e:
        _LOG.error(e)
        raise type(e) from e



async def get_warning(device_id: str = None):
    """Get warning messages from the projector"""

    _LOG.debug(f"Get warning messages for {device_id}")

    try:
        response = await projector_def(device_id).command(ADCP.Get.WARNING)
        if response:
            try:
                warning_msg_json = json.loads(response)
                if isinstance(warning_msg_json, list):
                    warning_msgs = [
                        str(item).replace("warn", "warning").replace("_", " ").title()
                        for item in warning_msg_json if item
                    ]
                    if warning_msgs:
                        return ", ".join(warning_msgs)
                    _LOG.warning(f"No warning message data found in response: {response}")
            except json.JSONDecodeError as e:
                _LOG.error(f"Failed to parse warning message response: {e}")
                _LOG.debug(f"Raw response: {response}")
    except Exception as e:
        _LOG.error(e)
        raise type(e) from e



async def get_resolution(device_id: str):
    """Get the current video input resolution from the projector and return it as a string"""

    _LOG.debug(f"Get current video input resolution for {device_id}")
    try:
        signal = await projector_def(device_id).command(ADCP.Get.SIGNAL)
        signal = signal.replace('"', "").replace("/", " / ")
    except Exception as e:
        raise type(e)(str(e)) from e
    return signal



async def get_dynamic_range(device_id: str):
    """Get the current dynamic range (sdr, hdr10, hlg) from the projector and return it as a string"""

    _LOG.debug(f"Get current dynamic range for {device_id}")
    try:
        dyn_range = await projector_def(device_id).command(ADCP.Get.HDR_FORMAT)
        dyn_range = dyn_range.replace('"', "")
        dyn_range = dyn_range.upper()
    except (OSError, NameError): #HDR Format command is temporally unavailable or not supported means range is SDR
        dyn_range = "SDR"
    except Exception as e:
        raise type(e)(str(e)) from e
    return dyn_range



async def get_color_space(device_id: str):
    """Get the current color space from the projector and return it as a string"""

    _LOG.debug(f"Get current color space for {device_id}")
    try:
        color_space = await projector_def(device_id).command(ADCP.Get.COLOR_SPACE)
        color_space = color_space.replace('"', "").upper().replace("BT", "BT.")
    except Exception as e:
        raise type(e)(str(e)) from e
    return color_space



async def get_color_format(device_id: str):
    """Get the current color format from the projector and return it as a string"""

    _LOG.debug(f"Get current color format for {device_id}")
    try:
        color_format = await projector_def(device_id).command(ADCP.Get.COLOR_FORMAT)
        color_format = color_format.replace('"', "").upper().replace("YCBCR", "YCbCr")
        # Convert YcbCr422 to YCbCr 4:2:2
        color_format = re.sub(r"(\d)", r" \1:", color_format, count=1)
        color_format = re.sub(r"(?<=\d)(\d)", r":\1", color_format)
        color_format = color_format.rstrip(":")
    except Exception as e:
        raise type(e)(str(e)) from e
    return color_format



async def get_mode_2d_3d(device_id: str):
    """Get the current 2d/3d mode from the projector and return it as a string"""

    _LOG.debug(f"Get current 2d/3d mode for {device_id}")
    try:
        mode = await projector_def(device_id).command(ADCP.Get.MODE_2D_3D)
        mode = mode.replace('"', "")
        mode = mode.upper()
    except (OSError, NameError): #3D status command is temporally unavailable or not supported means mode is 2D
        mode = "2D"
    except Exception as e:
        raise type(e)(str(e)) from e
    return mode



async def send_cmd(device_id: str, cmd_name:str, params = None):
    """Send a command to the projector and raise an exception if it fails"""

    projector_adcp = projector_def(device_id)

    if cmd_name in (config.SimpleCommands.UPDATE_VIDEO_INFO, ucapi.media_player.Commands.PLAY_PAUSE):
        try:
            await sensor.update_video(device_id)
            await media_player.update_video(device_id)
        except Exception as e:
            raise type(e)(str(e))

    elif cmd_name == config.SimpleCommands.UPDATE_HEALTH_STATUS:
        try:
            await sensor.update_light(device_id)
            await sensor.update_temp(device_id)
            await sensor.update_system(device_id)
        except Exception as e:
            raise type(e)(str(e))

    elif cmd_name == ucapi.media_player.Commands.SELECT_SOURCE:
        source = params["source"]

        try:
            if source == config.Sources.HDMI_1:
                await projector_adcp.command(f"{ADCP.Commands.INPUT.value} {ADCP.Values.Inputs.HDMI1.value}")
            elif source == config.Sources.HDMI_2:
                await projector_adcp.command(f"{ADCP.Commands.INPUT.value} {ADCP.Values.Inputs.HDMI2.value}")
            else:
                raise ValueError("Unknown source: " + source)
        except Exception as e:
            raise type(e)(str(e))

    elif cmd_name in (ucapi.media_player.Commands.MUTE_TOGGLE, config.SimpleCommands.PICTURE_MUTING_TOGGLE):
        try:
            mute_state = await get_attr_muted(device_id)
        except Exception as e:
            raise type(e)(str(e))

        try:
            if mute_state is False:
                await projector_adcp.command(f"{ADCP.Commands.MUTE.value} {ADCP.Values.States.ON.value}")
            elif mute_state is True:
                await projector_adcp.command(f"{ADCP.Commands.MUTE.value} {ADCP.Values.States.OFF.value}")
        except Exception as e:
            raise type(e)(str(e))

    else:
        try:
            adcp_cmd = config.UC2ADCP.get(cmd_name)
        except KeyError as k:
            if not any(cmd_name == item.value for item in ucapi.media_player.Commands):
                _LOG.info(f"Could't find a matching entity or simple command. \"{cmd_name}\" could be a native ADCP command. Skipping conversion")
                try:
                    await projector_adcp.command(cmd_name)
                except Exception as e:
                    raise type(e)(str(e))
            else:
                _LOG.error(f"Command \"{cmd_name}\" is not supported or implemented")
                raise KeyError() from k
        except Exception as e:
            _LOG.error("Could not map UC command to ADCP command")
            raise Exception(e) from e
        else:
            _LOG.debug(f"Mapped UC command \"{cmd_name}\" to ADCP command \"{adcp_cmd}\"")
            try:
                await projector_adcp.command(adcp_cmd)
            except Exception as e:
                raise type(e)(str(e))

    try:
        await update_attributes(device_id, cmd_name)
    except Exception as e:
        #No exception as this is not a critical error. The command itself was sent successfully. Not all query commands are supported by all projector models
        _LOG.error(f"Failed to update attributes for device {device_id} after command {cmd_name}: {e}")



async def update_attributes(device_id:str , cmd_name:str):
    """Update media player, remote and sensor entity attributes and values if the command changes or could potentially change these attributes or values"""

    mp_id = device_id
    rt_id = config.Devices.get(device_id=device_id, key="remote-id")

    match cmd_name:

        case ucapi.media_player.Commands.ON:
            try:
                if driver.api.configured_entities.get(mp_id) is not None:
                    driver.api.configured_entities.update_attributes(mp_id, {ucapi.media_player.Attributes.STATE: ucapi.media_player.States.ON})
                if driver.api.configured_entities.get(rt_id) is not None:
                    driver.api.configured_entities.update_attributes(rt_id, {ucapi.remote.Attributes.STATE: ucapi.remote.States.ON})
                await sensor.update_light(device_id)
                await sensor.update_temp(device_id)
                await sensor.update_system(device_id)
                await sensor.update_video(device_id)
                await media_player.update_video(device_id)
            except Exception as e:
                raise type(e)(str(e))
            _LOG.info("Media player and remote entity power status attribute set to \"ON\"")

        case ucapi.media_player.Commands.OFF:
            try:
                if driver.api.configured_entities.get(mp_id) is not None:
                    driver.api.configured_entities.update_attributes(mp_id, {ucapi.media_player.Attributes.STATE: ucapi.media_player.States.OFF})
                if driver.api.configured_entities.get(rt_id) is not None:
                    driver.api.configured_entities.update_attributes(rt_id, {ucapi.remote.Attributes.STATE: ucapi.remote.States.OFF})
                await sensor.update_light(device_id)
                await sensor.update_temp(device_id)
                await sensor.update_system(device_id)
                await sensor.update_video(device_id)
                await media_player.update_video(device_id)
            except Exception as e:
                raise type(e)(str(e))
            _LOG.info("Media player and remote entity power status attribute set to \"OFF\"")

        case ucapi.media_player.Commands.TOGGLE:
            await driver.asyncio.sleep(3)  # Wait 3 seconds for the projector to report the correct power state
            try:
                power_state = await get_attr_power(device_id)
            except Exception as e:
                _LOG.error(e)
                _LOG.warning("Couldn't get power state. Set to unknown")
                power_state = {ucapi.media_player.Attributes.STATE: ucapi.media_player.States.UNKNOWN}

            if driver.api.configured_entities.get(mp_id) is not None:
                driver.api.configured_entities.update_attributes(mp_id, power_state)
            if driver.api.configured_entities.get(rt_id) is not None:
                driver.api.configured_entities.update_attributes(rt_id, power_state)
            await sensor.update_light(device_id)
            await sensor.update_temp(device_id)
            await sensor.update_system(device_id)
            await sensor.update_video(device_id)
            await media_player.update_video(device_id)

            _LOG.info(f"Media player and remote entity power status attribute set to \"{power_state}\"")

        case \
            ucapi.media_player.Commands.MUTE | \
            ucapi.media_player.Commands.UNMUTE | \
            ucapi.media_player.Commands.MUTE_TOGGLE | \
            config.SimpleCommands.PICTURE_MUTING_TOGGLE:

            try:
                mute_state = await get_attr_muted(device_id)
            except Exception as e:
                raise type(e)(str(e))

            try:
                if mute_state is False:
                    driver.api.configured_entities.update_attributes(mp_id, {ucapi.media_player.Attributes.MUTED: False})
                    _LOG.info("Media player mute status attribute set to \"False\"")
                    await sensor.update_video(device_id)
                    await media_player.update_video(device_id)
                elif mute_state is True:
                    driver.api.configured_entities.update_attributes(mp_id, {ucapi.media_player.Attributes.MUTED: True})
                    _LOG.info("Media player mute status attribute set to \"True\"")
                    await sensor.update_video(device_id)
                    await media_player.update_video(device_id)
            except Exception as e:
                raise type(e)(str(e))

        case \
            ucapi.media_player.Commands.SELECT_SOURCE | \
            config.SimpleCommands.INPUT_HDMI1 | \
            config.SimpleCommands.INPUT_HDMI2:

            try:
                source = await get_attr_source(device_id)
            except Exception as e:
                raise type(e)(str(e))

            try:
                if source == config.Sources.HDMI_1:
                    driver.api.configured_entities.update_attributes(mp_id, {ucapi.media_player.Attributes.SOURCE: source})
                    _LOG.info(f"Media player source attribute update to \"{source}\"")
                    await sensor.update_video(device_id)
                    await media_player.update_video(device_id)
                elif source == config.Sources.HDMI_2:
                    driver.api.configured_entities.update_attributes(mp_id, {ucapi.media_player.Attributes.SOURCE: source})
                    _LOG.info(f"Media player source attribute update to \"{source}\"")
                    await sensor.update_video(device_id)
                    await media_player.update_video(device_id)
                else:
                    raise ValueError("Unknown source: " + source)
            except Exception as e:
                raise type(e)(str(e))
