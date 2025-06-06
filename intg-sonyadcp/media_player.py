#!/usr/bin/env python3

"""Module that includes functions to add a projector media player entity, poll attributes and the media player command handler"""

import logging
from typing import Any

import ucapi

import config
import driver
import projector

_LOG = logging.getLogger(__name__)



async def mp_cmd_handler(entity: ucapi.MediaPlayer, cmd_id: str, _params: dict[str, Any] | None) -> ucapi.StatusCodes:
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



async def add_mp(device_id: str):
    """Function to add a media player entity with the config.MpDef class definition"""

    mp_name = config.Devices.get(device_id=device_id, key="name")
    mp_id= device_id

    definition = config.MediaPlayer().get_def(ent_id=mp_id, name=mp_name)

    driver.api.available_entities.add(definition)

    _LOG.info(f"Added projector media player entity with id {mp_id} and name {mp_name} as available entity")



async def remove_mp(device_id: str):
    """Function to remove a media player entity with the config.MpDef class definition"""

    mp_name = config.Devices.get(device_id=device_id, key="name")
    mp_id= device_id

    definition = config.MediaPlayer().get_def(ent_id=mp_id, name=mp_name)

    driver.api.available_entities.add(definition)

    _LOG.info(f"Removed projector media player entity with id {mp_id} and name {mp_name} as available entity")



class MpPollerController:
    """Creates a task to regularly poll power/mute/input attributes from the projector"""

    @staticmethod
    async def start(device_id: str):
        """Starts the mp_poller task. If the task is already running it will be stopped and restarted"""

        name = device_id + "-mp_poller"
        mp_poller_interval = config.Devices.get(device_id=device_id, key="mp_poller_interval")
        if mp_poller_interval is None:
            mp_poller_interval = config.Setup.get("default_mp_poller_interval")

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
        if config.Setup.get("standby"):
            continue
        try:
            #TODO Implement check if there are too many timeouts/connection errors to the projector and automatically deactivate poller and set entity status to unknown
            await update_mp(device_id)
        except Exception as e:
            _LOG.error(e)
            continue



async def update_mp(device_id: str):
    """Retrieve input source, power status and muted status from the projector, compare them with the known status on the remote and update them if necessary"""

    try:
        _LOG.debug(f"Checking power/mute/input status for media player attributes poller task for {device_id}")
        power = await projector.get_attr_power(device_id)
        muted = await projector.get_attr_muted(device_id)
        source = await projector.get_attr_source(device_id)
    except Exception as e:
        power = {ucapi.remote.Attributes.STATE: ucapi.remote.States.UNAVAILABLE}
        raise Exception(f"Could not check power/mute/input state for {device_id}: {e}") from e

    try:
        stored_states = await driver.api.available_entities.get_states()
    except Exception as e:
        raise Exception(e) from e

    if stored_states != []:
        attributes_stored = stored_states[0]["attributes"] # [0] = 1st entity that has been added
    else:
        raise Exception("Got empty states from remote. Please make sure to add configured entities")

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

    if not attributes_to_skip:
        _LOG.debug(f"Entity attributes for {str(attributes_to_skip)} on {device_id} have not changed since the last update")

    if not attributes_to_update:
        attributes_to_send = {}
        if "state" in attributes_to_update:
            attributes_to_send.update({ucapi.media_player.Attributes.STATE: power})
        if "muted" in attributes_to_update:
            attributes_to_send.update({ucapi.media_player.Attributes.MUTED: muted})
        if "source" in attributes_to_update:
            attributes_to_send.update({ucapi.media_player.Attributes.SOURCE: source})

        try:
            api_update_attributes = driver.api.configured_entities.update_attributes(device_id, attributes_to_send)
        except Exception as e:
            raise Exception("Error while updating attributes for entity id " + device_id) from e

        if not api_update_attributes:
            raise Exception("Entity " + device_id + " not found. Please make sure it's added as a configured entity on the remote")
        else:
            _LOG.info(f"Updated entity attribute(s) {str(attributes_to_update)} for {device_id}")

    else:
        _LOG.debug(f"No projector attributes for {device_id} to update. Skipping update process")
