#!/usr/bin/env python3

"""Module that includes functions to add a light source timer sensor entity and to poll the sensor data"""

import logging

import ucapi

import config
import driver
import projector

_LOG = logging.getLogger(__name__)



async def add_lt_sensor(device_id: str):
    """Function to add a light source timer sensor entity with the config.sensorDef class definition and get current light source hours"""

    lt_name = config.Devices.get(device_id=device_id, key="lt-name")
    lt_id = config.Devices.get(device_id=device_id, key="lt-id")

    definition = config.LSTSensor().get_def(ent_id=lt_id, name=lt_name)

    driver.api.available_entities.add(definition)

    _LOG.info(f"Added projector light source timer sensor entity with id {lt_id} and name {lt_name} as available entity")



async def remove_lt_sensor(device_id: str):
    """Function to remove a light source timer sensor entity with the config.sensorDef class definition and get current light source hours"""

    lt_name = config.Devices.get(device_id=device_id, key="lt-name")
    lt_id = config.Devices.get(device_id=device_id, key="lt-id")

    definition = config.LSTSensor().get_def(ent_id=lt_id, name=lt_name)

    driver.api.available_entities.add(definition)

    _LOG.info(f"Removed projector light source timer sensor entity with id {lt_id} and name {lt_name} as available entity")



class LtPollerController():
    """(Re)Starts or stops a task to regularly poll light source times from the projector"""

    @staticmethod
    async def start(device_id: str):
        """Starts the lt_poller task. If the task is already running it will be stopped and restarted"""

        name = device_id + "-lt_poller"
        lt_poller_interval = config.Devices.get(device_id=device_id, key="lt_poller_interval")
        if lt_poller_interval is None:
            lt_poller_interval = config.Setup.get("default_lt_poller_interval")

        if lt_poller_interval == 0:
            _LOG.debug("Light source hours poller interval set to " + str(lt_poller_interval))
            try:
                poller_task, = [task for task in driver.asyncio.all_tasks() if task.get_name() == name]
                poller_task.cancel()
                try:
                    await poller_task
                except driver.asyncio.CancelledError:
                    _LOG.info(f"Stopped running light source hours poller task \"{name}\"")
            except ValueError:
                _LOG.info(f"The light source hours poller task for device_id \"{device_id}\" will not be started")
        else:
            try:
                poller_task, = [task for task in driver.asyncio.all_tasks() if task.get_name() == name]
                poller_task.cancel()
                try:
                    await poller_task
                except driver.asyncio.CancelledError:
                    driver.loop.create_task(lt_poller(device_id, lt_poller_interval), name=name)
                    _LOG.info(f"Restarted light source hours poller task \"{name}\" with an interval of {str(lt_poller_interval)} seconds")
            except ValueError:
                driver.loop.create_task(lt_poller(device_id, lt_poller_interval), name=name)
                _LOG.info(f"Started light source hours poller task \"{name}\" with an interval of {str(lt_poller_interval)} seconds")

    @staticmethod
    async def stop(device_id:str = None):
        """Stops the lt_poller task for the given device_id"""

        async def stop_task(name):
            try:
                poller_task, = [task for task in driver.asyncio.all_tasks() if task.get_name() == name]
                poller_task.cancel()
                try:
                    await poller_task
                except driver.asyncio.CancelledError:
                    _LOG.debug(f"Stopped light source hours poller task \"{name}\"")
            except ValueError:
                if device_id is not None:
                    _LOG.debug(f"There is no running light source hours poller task named \"{name}\"")

        if device_id is None:
            _LOG.debug("No device_id provided. Stopping all mp poller tasks")
            for device in config.Devices.list():
                name = str(device) + "-lt_poller"
                await stop_task(name)
        else:
            name = device_id + "-lt_poller"
            await stop_task(name)



async def lt_poller(device_id: str, interval:int) -> None:
    """Projector light source timer poller task. Runs only when the projector is powered on"""
    while True:
        await driver.asyncio.sleep(interval)
        if config.Setup.get("standby"):
            continue
        try:
            _LOG.debug("Checking power status for light source timer sensor")
            projector_power = await projector.get_attr_power(device_id)
            if projector_power == {ucapi.media_player.Attributes.STATE: ucapi.media_player.States.OFF}:
                _LOG.debug("Skip updating light source timer. Projector is powered off")
                continue
        except Exception as e:
            #TODO Implement check if there are too many timeouts/connection errors to the projector and automatically deactivate poller and set entity status to unknown
            _LOG.error(e)
            continue
        try:
            #TODO Add check if network and remote is reachable
            await update_lt(device_id)
        except Exception as e:
            _LOG.error(e)
            continue



async def update_lt(device_id: str):
    """Update light source timer sensor. Compare retrieved light source hours with the last sensor value from the remote and update it if necessary"""

    lt_id = config.Devices.get(device_id=device_id, key="lt-id")

    try:
        current_value = await projector.get_light_source_hours(device_id)
    except Exception as e:
        _LOG.warning(f"Failed to get light source hours from {device_id}. Use empty sensor value")
        current_value = ""
        raise Exception(e) from e

    try:
        stored_states = await driver.api.available_entities.get_states()
    except Exception as e:
        raise Exception(e) from e

    if stored_states != []:
        attributes_stored = stored_states[1]["attributes"] # [1] = 2nd entity that has been added
    else:
        raise Exception(f"Got empty states for {device_id} from remote. Please make sure to add configured entities")

    try:
        stored_value = attributes_stored["value"]
    except KeyError as e:
        _LOG.info(f"Light source timer sensor value for {device_id} has not been set yet")
        stored_value = "0"

    if current_value == "":
        _LOG.warning(f"Couldn't get light source hours for {device_id}. Set status to Unknown")
        attributes_to_send = {ucapi.sensor.Attributes.STATE: ucapi.sensor.States.UNKNOWN, ucapi.sensor.Attributes.VALUE: current_value, ucapi.sensor.Attributes.UNIT: "h"}
    else:
        attributes_to_send = {ucapi.sensor.Attributes.STATE: ucapi.sensor.States.ON, ucapi.sensor.Attributes.VALUE: current_value, ucapi.sensor.Attributes.UNIT: "h"}

    if stored_value == current_value:
        _LOG.debug(f"Light source hours for {device_id} have not changed since the last update. Skipping update process")
    else:
        try:
            api_update_attributes = driver.api.configured_entities.update_attributes(lt_id, attributes_to_send)
        except Exception as e:
            _LOG.error(e)
            raise Exception("Error while updating sensor value for entity id " + lt_id) from e

        if not api_update_attributes:
            raise Exception("Sensor entity " + lt_id + " not found. Please make sure it's added as a configured entity on the remote")

        _LOG.info(f"Updated light source timer for {device_id} sensor value to " + str(current_value))
