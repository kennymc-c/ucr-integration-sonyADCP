#!/usr/bin/env python3

"""Module that includes functions to add a projector media player entity, poll attributes and the media player command handler"""

import logging
from typing import Any

import ucapi

import config
import driver
import projector
import adcp as ADCP

_LOG = logging.getLogger(__name__)



async def add(device_id: str):
    """Function to add a media player entity with the config.MpDef class definition"""

    mp_name = config.Devices.get(device_id=device_id, key=config.DevicesKeys.NAME)
    mp_id= device_id

    definition = config.EntityDefinitions.MediaPlayer().get_def(ent_id=mp_id, name=mp_name)

    driver.api.available_entities.add(definition)

    _LOG.info(f"Added projector media player entity with id {mp_id} and name {mp_name} as available entity")



async def remove(device_id: str):
    """Function to remove a media player entity with the config.MpDef class definition"""

    mp_name = config.Devices.get(device_id=device_id, key=config.DevicesKeys.NAME)
    mp_id= device_id

    definition = config.EntityDefinitions.MediaPlayer().get_def(ent_id=mp_id, name=mp_name)

    driver.api.available_entities.add(definition)

    _LOG.info(f"Removed projector media player entity with id {mp_id} and name {mp_name} as available entity")



async def cmd_handler(entity: ucapi.MediaPlayer, cmd_id: str, _params: dict[str, Any] | None) -> ucapi.StatusCodes:
    """
    Media Player command handler.

    Called by the integration-API if a command is sent to a configured media_player-entity.

    :param entity: media_player entity
    :param cmd_id: command
    :param _params: optional command parameters
    :return: status of the command
    """

    try:
        if not _params:
            _LOG.info(f"Received {cmd_id} command for {entity.id}")
            await projector.send_cmd(entity.id, cmd_id)
        else:
            _LOG.info(f"Received {cmd_id} command with parameter {_params} for {entity.id}")
            await projector.send_cmd(entity.id, cmd_id, _params)
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



class MpPollerController:
    """Creates a task to regularly poll power/mute/input attributes from the projector"""

    @staticmethod
    async def start(device_id: str):
        """Starts the mp_poller task. If the task is already running it will be stopped and restarted"""

        name = device_id + "-mp_poller"
        mp_poller_interval = config.Devices.get(device_id=device_id, key=config.DevicesKeys.MP_POLLER_INTERVAL)
        if mp_poller_interval is None:
            mp_poller_interval = config.Setup.get(config.Setup.Keys.DEFAULT_POLLER_INTERVAL_MEDIA_PLAYER)

        if mp_poller_interval == 0:
            _LOG.debug("Power/mute/input hours poller interval set to " + str(mp_poller_interval))
            try:
                poller_task, = [task for task in driver.asyncio.all_tasks() if task.get_name() == name]
                poller_task.cancel()
                try:
                    await poller_task
                except driver.asyncio.CancelledError:
                    _LOG.info(f"Stopped running power/mute/input poller task \"{name}\"")
            except ValueError:
                _LOG.info(f"The power/mute/input poller task for device_id \"{device_id}\" will not be started")
        else:
            try:
                poller_task, = [task for task in driver.asyncio.all_tasks() if task.get_name() == name]
                poller_task.cancel()
                try:
                    await poller_task
                except driver.asyncio.CancelledError:
                    driver.loop.create_task(mp_poller(device_id, mp_poller_interval), name=name)
                    _LOG.info(f"Restarted power/mute/input poller task \"{name}\" with an interval of {str(mp_poller_interval)} seconds")
            except ValueError:
                driver.loop.create_task(mp_poller(device_id, mp_poller_interval), name=name)
                _LOG.info(f"Started power/mute/input poller task \"{name}\" with an interval of {str(mp_poller_interval)} seconds")

    @staticmethod
    async def stop(device_id:str = None):
        """Stops the mp_poller task for the given device_id"""

        async def stop_task(name):
            try:
                poller_task, = [task for task in driver.asyncio.all_tasks() if task.get_name() == name]
                poller_task.cancel()
                try:
                    await poller_task
                except driver.asyncio.CancelledError:
                    _LOG.debug(f"Stopped power/mute/input poller task \"{name}\"")
            except ValueError:
                if device_id is not None:
                    _LOG.debug(f"There is no running power/mute/input poller task named \"{name}\"")

        if device_id is None:
            _LOG.debug("No device_id provided. Stopping all mp poller tasks")
            for device in config.Devices.list():
                name = str(device) + "-mp_poller"
                await stop_task(name)
        else:
            name = device_id + "-mp_poller"
            await stop_task(name)



async def mp_poller(device_id: str, interval: int) -> None:
    """Projector attributes poller task"""
    while True:
        await driver.asyncio.sleep(interval)
        if config.Setup.get(config.Setup.Keys.STANDBY):
            continue
        try:
            #TODO Implement check if there are too many timeouts/connection errors to the projector and automatically deactivate poller and set entity status to unknown
            await update_attributes(device_id)
        except Exception as e:
            _LOG.error(e)
            continue



async def update_attributes(device_id: str):
    """Retrieve input source, power status and muted status from the projector, compare them with the current entity attributes and update them if necessary"""

    if driver.api.configured_entities.get(device_id) is None:
        _LOG.info(f"Entity {device_id} not found in configured entities. Skip updating attributes")
        return True

    _LOG.debug(f"Checking power/mute/input status for media player attributes for {device_id}")
    try:
        try:
            power = await projector.get_setting(device_id, config.SensorTypes.POWER_STATUS)
        except Exception as e:
            _LOG.error(e)
            _LOG.error(f"Can't get power state from projector. Set state to {ucapi.media_player.States.UNKNOWN}")
            power = ucapi.media_player.States.UNKNOWN

        try:
            muted = await projector.get_setting(device_id, config.SensorTypes.PICTURE_MUTING)
        except Exception as e:
            _LOG.error(e)
            _LOG.error("Can't get picture muting state from projector. Set state to False")
            muted = False

        try:
            source = await projector.get_setting(device_id, config.SensorTypes.INPUT)
        except Exception as e:
            _LOG.error(e)
            _LOG.error(f"Can't get input from projector. Set input to {config.Messages.ERROR}")
            source = config.Messages.ERROR

    except OSError as e:
        raise OSError(e) from e
    except Exception as e:
        _LOG.error(f"Can't get power state from projector. Set state to {ucapi.media_player.States.UNKNOWN}")
        power = ucapi.media_player.States.UNKNOWN
        raise Exception(e) from e

    if muted == ADCP.Values.States.OFF.replace("\"",""):
        muted = False
    else:
        muted = True

    if source == ADCP.Values.Inputs.HDMI1.replace("\"",""):
        source = config.Sources.HDMI_1
    elif source == ADCP.Values.Inputs.HDMI2.replace("\"",""):
        source = config.Sources.HDMI_2
    else:
        source = config.Sources.UNKNOWN

    try:
        stored_states = await driver.api.available_entities.get_states()
    except Exception as e:
        raise Exception(e) from e

    if stored_states != []:
        attributes_stored = next((state["attributes"] for state in stored_states if state["entity_id"] == device_id),None)
    else:
        raise Exception(f"Got empty states for {device_id} from remote")

    stored_attributes = {"state": attributes_stored["state"], "muted": attributes_stored["muted"], "source": attributes_stored["source"]}
    current_attributes = {"state": power, "muted": muted, "source": source}

    attributes_to_check = ["state", "muted", "source"]
    attributes_to_update = []
    attributes_to_skip = []

    for attribute in attributes_to_check:
        if current_attributes[attribute] != stored_attributes[attribute]:
            attributes_to_update.append(attribute)
        else:
            attributes_to_skip.append(attribute)

    if attributes_to_skip:
        _LOG.debug(f"Entity attributes for {str(attributes_to_skip)} on {device_id} have not changed since the last update")

    if attributes_to_update:
        attributes_to_send = {}
        if "state" in attributes_to_update:
            attributes_to_send.update({ucapi.media_player.Attributes.STATE: power})
        if "muted" in attributes_to_update:
            attributes_to_send.update({ucapi.media_player.Attributes.MUTED: muted})
        if "source" in attributes_to_update:
            attributes_to_send.update({ucapi.media_player.Attributes.SOURCE: source})

        try:
            driver.api.configured_entities.update_attributes(device_id, attributes_to_send)
        except Exception as e:
            raise Exception("Error while updating attributes for entity id " + device_id) from e

        _LOG.info(f"Updated entity attribute(s) {str(attributes_to_update)} for {device_id}")

    else:
        _LOG.debug(f"No media player attributes for {device_id} to update. Skipping update process")
