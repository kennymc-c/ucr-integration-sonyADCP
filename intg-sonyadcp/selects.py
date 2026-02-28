#!/usr/bin/env python3

"""Module that includes functions to add/remove select entities and to poll the data"""

import logging
from typing import Any

import ucapi

import config
import driver
import projector

_LOG = logging.getLogger(__name__)



async def add(device_id: str, select_type: str):
    """Function to add a select entity for the given select type. Will check if the select type is supported by the projector before adding it.
    
    :param device_id: The device ID of the projector
    :param select_type: The type of the sensor to add. Possible values are config.Setup["select_types"]
    """

    try:
        select_name = config.Devices.get(device_id=device_id, key="select-"+select_type+"-name")
        select_id = config.Devices.get(device_id=device_id, key="select-"+select_type+"-id")
        select_attributes = {ucapi.select.Attributes.STATE: ucapi.select.States.ON}

        if select_type not in config.SelectTypes.get_all():
            _LOG.error(f"Select type {select_type} is not valid. Cannot add select entity for {device_id}. Valid types are {str(config.Setup.get('select_types'))}")
            return

        _LOG.debug(f"Checking if {select_type} is a valid setting for {device_id}")
        try:
            await projector.get_setting(device_id, setting=select_type)
        except NameError:
            _LOG.info(f"Setting {select_type} is not supported for this model. The select entity will not be added as available entity")
            return
        except OSError:
            _LOG.info(f"Could not get a value for {select_type}. Either because the projector is powered off or the current signal doesn't support this setting or mode")
            _LOG.info("This select entity will be updated when the projector is powered on or the input is changed")
        except Exception as e:
            error_msg = str(e)
            if error_msg:
                _LOG.debug(e)
            _LOG.warning(f"Error while checking if setting {select_type} is valid for {device_id}. \
Adding select entity anyway. It will be updated when the projector is reachable")

        definition = ucapi.Select(
            select_id,
            select_name,
            attributes=select_attributes,
            cmd_handler=cmd_handler
        )

        driver.api.available_entities.add(definition)

        _LOG.info(f"Added projector select entity with id {select_id} and name {select_name} as available entity")

    except Exception as e:
        error_msg = str(e)
        _LOG.error(f"Error while adding select entity {select_type} for device {device_id}. Select will not be available until integration is restarted")
        if error_msg:
            _LOG.error(f"Exception details: {e}")



async def remove(device_id: str, select_type: str):
    """Function to remove a select entity with the config select class definition
    
    :param device_id: The device ID of the projector
    :param select_type: The type of the select entity to remove. Possible values are config.Setup["select_types"]
    """

    if select_type not in config.SelectTypes.get_all():
        _LOG.error(f"Select type {select_type} is not valid. Cannot remove select entity for device_id {device_id}. Valid types are {str(config.Setup.get('select_types'))}")
        return

    select_id = config.Devices.get(device_id=device_id, key="select-"+select_type+"-id")
    select_name = config.Devices.get(device_id=device_id, key="select-"+select_type+"-name")

    driver.api.available_entities.remove(select_id)

    _LOG.info(f"Removed projector select entity with id {select_id} and name {select_name} as available entity")



async def update_attributes(device_id: str, select_type: str):
    """Function to update all attributes of the given select entity for the given select type."""

    select_id = config.Devices.get(device_id=device_id, key=f"select-{select_type}-id")

    _LOG.debug(f"Updating attributes for select entity {select_id}")

    options_prettified = None
    current_option_prettified = None

    try:
        options = await projector.get_setting_options(device_id, setting=select_type)
        current_option = await projector.get_setting(device_id, setting=select_type)
    except OSError:
        _LOG.info(f"Could not temporarily get options for setting \"{select_type}\". \
Either because the projector is powered off or the current signal doesn't support this setting or mode")
        _LOG.info(f"State and options for select entity {select_id} will be updated when the projector is powered on or the input is changed")
        _LOG.debug(f"Setting state to \"{ucapi.select.States.UNKNOWN}\" and options to \"{config.Messages.TEMPORARILY_UNAVAILABLE}\" until options can be retrieved")
        attributes = {
                    ucapi.select.Attributes.STATE: ucapi.select.States.UNKNOWN,
                    ucapi.select.Attributes.OPTIONS: [config.Messages.TEMPORARILY_UNAVAILABLE],
                    ucapi.select.Attributes.CURRENT_OPTION: config.Messages.TEMPORARILY_UNAVAILABLE
                    }
    except Exception as e:
        error_msg = str(e)
        if error_msg:
            _LOG.error(f"Exception details: {e}")
        _LOG.error(f"Error while retrieving options for select entity {select_id}. Options will not be updated")
        return
    else:
        options_prettified = config.convert_options(options)
        current_option_prettified = config.convert_options(current_option)
        attributes = {
                ucapi.select.Attributes.STATE: ucapi.select.States.ON,
                ucapi.select.Attributes.OPTIONS: options_prettified,
                ucapi.select.Attributes.CURRENT_OPTION: current_option_prettified
                }

    #BUG WORKAROUND Always send DeviceStates.CONNECTED when updating select entity attributes
    await driver.api.set_device_state(ucapi.DeviceStates.CONNECTED)

    try:
        driver.api.available_entities.update_attributes(select_id, attributes)
    except Exception as e:
        error_msg = str(e)
        _LOG.error(f"Error while updating attributes for select entity {select_id}")
        if error_msg:
            _LOG.error(f"Exception details: {e}")

    if options_prettified is not None and current_option_prettified is not None:
        _LOG.debug(f"Updated attributes for select entity {select_id}: options={options_prettified}, current_option={ current_option_prettified}")
    else:
        _LOG.debug(f"Updated attributes for select entity {select_id}")



async def update_all_selects(device_id:str):
    """Update all select entity option attributes for a specific device"""
    for select_type in config.SelectTypes.get_all():
        select_id = f"select-{select_type}-{device_id}"
        if driver.api.available_entities.contains(select_id):
            try:
                await update_attributes(device_id, select_type)
            except Exception as e:
                error_msg = str(e)
                if error_msg:
                    _LOG.warning(f"Failed to update {select_type} sensor value for {device_id}")
                    _LOG.warning(error_msg)
                else:
                    _LOG.warning(f"Failed to update {select_type} sensor value for {device_id}")
        else:
            _LOG.debug(f"{select_id} is not an available entity. Skip updating attributes")



async def get_options(device_id, setting):
    "Get and return all and current options for the give setting as a tuple"
    try:
        all_options = await projector.get_setting_options(device_id, setting)
    except OSError as o:
        _LOG.error(f"Command {setting} temporarily unavailable")
        raise Exception from o

    try:
        current_option = await projector.get_setting(device_id, setting)
    except Exception:
        raise

    return all_options, current_option



async def cmd_handler(entity: ucapi.Select, cmd_id: str, params: dict[str, Any] | None) -> ucapi.StatusCodes:
    """Command handler for select entities to set the selected option on the projector
    
    :param entity: The select entity for which the command was triggered
    :param cmd_id: The command that was triggered. Possible values are defined in ucapi.select.Commands
    :param _params: The parameters of the command. 
    :return: The status code of the command execution.
    """

    if not params:
        _LOG.info(f"Received {cmd_id} command for {entity.id}")
    else:
        _LOG.info(f"Received {cmd_id} command with parameter {params} for {entity.id}")

    #setting = entity.id.removeprefix("select-").split("-VPL", 1)[0]
    setting = "-".join(parts[1:next(i for i, p in enumerate(parts) if i > 0 and p.isupper())]) if (parts := entity.id.split("-"))[0] == "select" else None
    device_id = entity.id.replace(f"select-{setting}","").removeprefix("-")

    cycle = True #Using the same cycle=True default as HA as this parameter currently can't be changed by the user
    if params:
        try:
            if params["cycle"] == "false":
                cycle = False
                _LOG.warning("Cycle parameter is enabled for this command but it is currently ignored")
        except KeyError:
            pass #BUG Cycle parameter currently not included in web configurator or commands
        #although it's not labeled as a planned feature in the core-api docs

    match cmd_id:

        case ucapi.select.Commands.SELECT_OPTION:
            option = params["option"] if params else None

        case ucapi.select.Commands.SELECT_FIRST:
            try:
                all_options, current_option = await get_options(device_id, setting)
            except Exception:
                return ucapi.StatusCodes.BAD_REQUEST
            option = all_options[0]

        case ucapi.select.Commands.SELECT_LAST:
            try:
                all_options, current_option = await get_options(device_id, setting)
            except Exception:
                return ucapi.StatusCodes.BAD_REQUEST
            option = all_options[-1]

        case ucapi.select.Commands.SELECT_NEXT | ucapi.select.Commands.SELECT_PREVIOUS:
            try:
                all_options, current_option = await get_options(device_id, setting)
            except Exception:
                return ucapi.StatusCodes.BAD_REQUEST

            try:
                option_index = all_options.index(current_option)
            except ValueError:
                _LOG.warning("Couldn't retrieve the current option. Will use the first option instead")
                option = all_options[0]

            last_index = len(all_options) - 1

            if cmd_id == ucapi.select.Commands.SELECT_NEXT:
                if option_index == last_index:
                    if not cycle:
                        _LOG.info("Reached the end of the options list. Won't cycle to the first option as cycling is disabled for this command")
                        return ucapi.StatusCodes.OK
                    next_index = 0
                else:
                    next_index = option_index + 1

                option = all_options[next_index]

            elif cmd_id == ucapi.select.Commands.SELECT_PREVIOUS:
                if option_index == 0:
                    if not cycle:
                        _LOG.info("Reached the beginning of the options list. Won't cycle to the last option as cycling is disabled for this command")
                        return ucapi.StatusCodes.OK
                    prev_index = last_index
                else:
                    prev_index = option_index - 1

                option = all_options[prev_index]

        case _ :
            _LOG.error(f"Unknown command: {cmd_id}")
            return ucapi.StatusCodes.NOT_FOUND

    if option == config.Messages.TEMPORARILY_UNAVAILABLE:
        _LOG.error(f"Command {setting} temporarily unavailable")
        return ucapi.StatusCodes.BAD_REQUEST

    command_adcp = config.UC2ADCP.get(setting)
    value_adcp = config.convert_options(option, reverse=True)

    if setting == config.SelectTypes.PICTURE_POSITION_SAVE:
        #pic_pos_save and del commands need different values than pic_pos_sel that is used to get the options
        value_adcp = value_adcp.replace("\"","")
        value_adcp = f"--{value_adcp}"

    command = {"command": command_adcp, "value": value_adcp, "setting": setting}

    try:
        if option is not None:
            _LOG.debug(f"Sending adcp command with setting name to {device_id}: {str(command)}")
            await projector.send_cmd(device_id, cmd_name=command)
        else:
            _LOG.error(f"No option could be determined for command {cmd_id} with params {params} for select entity {entity.id}")
            return ucapi.StatusCodes.BAD_REQUEST
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
        if error:
            _LOG.error(f"Failed to send command {cmd_id}: {error}")
        return ucapi.StatusCodes.BAD_REQUEST
    return ucapi.StatusCodes.OK
