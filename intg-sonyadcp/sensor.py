#!/usr/bin/env python3

"""Module that includes functions to add a light source timer sensor entity and to poll the sensor data"""

import logging

import ucapi

import config
import driver
import projector

_LOG = logging.getLogger(__name__)



async def add_lt_sensor(ent_id: str, name: str):
    """Function to add a light source timer sensor entity with the config.sensorDef class definition and get current light source hours"""

    definition = ucapi.Sensor(
        ent_id,
        name,
        features=None, #Mandatory although sensor entities have no features
        attributes=config.LTSensorDef.attributes,
        device_class=config.LTSensorDef.device_class,
        options=config.LTSensorDef.options
    )

    _LOG.debug("Projector light source timer sensor entity definition created")

    driver.api.available_entities.add(definition)

    _LOG.info("Added projector light source timer sensor entity as available entity")



class LtPollerController:
    """(Re)Starts or stops a task to regularly poll light source times from the projector"""

    @staticmethod
    async def start(ent_id: str, ip: str):
        """Starts the lt_poller task. If the task is already running it will be stopped and restarted"""
        lt_poller_interval = config.Setup.get("lt_poller_interval")
        if lt_poller_interval == 0:
            _LOG.debug("light source hours poller interval set to " + str(lt_poller_interval))
            try:
                poller_task, = [task for task in driver.asyncio.all_tasks() if task.get_name() == "lt_poller"]
                poller_task.cancel()
                try:
                    await poller_task
                except driver.asyncio.CancelledError:
                    _LOG.info("Stopped running light source hours poller task")
            except ValueError:
                _LOG.info("The light source hours poller task will not be started")
        else:
            try:
                poller_task, = [task for task in driver.asyncio.all_tasks() if task.get_name() == "lt_poller"]
                poller_task.cancel()
                try:
                    await poller_task
                except driver.asyncio.CancelledError:
                    driver.loop.create_task(lt_poller(ent_id, lt_poller_interval, ip), name="lt_poller")
                    _LOG.info("Restarted light source hours poller task with an interval of " + str(lt_poller_interval) + " seconds")
            except ValueError:
                driver.loop.create_task(lt_poller(ent_id, lt_poller_interval, ip), name="lt_poller")
                _LOG.info("Started light hours poller task with an interval of " + str(lt_poller_interval) + " seconds")

    @staticmethod
    async def stop():
        """Stops the lt_poller task"""
        try:
            poller_task, = [task for task in driver.asyncio.all_tasks() if task.get_name() == "lt_poller"]
            poller_task.cancel()
            try:
                await poller_task
            except driver.asyncio.CancelledError:
                _LOG.debug("Stopped light source hours poller task")
        except ValueError:
            _LOG.debug("Light source hours poller task is not running or will not be stopped \
as the sensor entity has been removed or not yet added as a configured entity on the remote")



async def lt_poller(entity_id: str, interval:int, ip: str) -> None:
    """Projector light source timer poller task. Runs only when the projector is powered on"""
    while True:
        await driver.asyncio.sleep(interval)
        if config.Setup.get("standby"):
            continue
        try:
            _LOG.debug("Checking power status for light source timer sensor")
            projector_power = await projector.get_attr_power(ip)
            if projector_power == {ucapi.media_player.Attributes.STATE: ucapi.media_player.States.OFF}:
                _LOG.debug("Skip updating light source timer. Projector is powered off")
                continue
        except Exception as e:
            #TODO Implement check if there are too many timeouts/connection errors to the projector and automatically deactivate poller and set entity status to unknown
            _LOG.error(e)
            continue
        try:
            #TODO Add check if network and remote is reachable
            await update_lt(entity_id, ip)
        except Exception as e:
            _LOG.error(e)
            continue



async def update_lt(entity_id: str, ip: str):
    """Update light source timer sensor. Compare retrieved light source hours with the last sensor value from the remote and update it if necessary"""
    try:
        current_value = await projector.get_light_source_hours(ip)
    except Exception as e:
        _LOG.warning("Failed to get light source hours from projector. Use empty sensor value")
        current_value = ""
        raise Exception(e) from e

    try:
        stored_states = await driver.api.available_entities.get_states()
    except Exception as e:
        raise Exception(e) from e

    if stored_states != []:
        attributes_stored = stored_states[1]["attributes"] # [1] = 2nd entity that has been added
    else:
        raise Exception("Got empty states from remote. Please make sure to add configured entities")

    try:
        stored_value = attributes_stored["value"]
    except KeyError as e:
        _LOG.info("Light source timer sensor value has not been set yet")
        stored_value = "0"

    if current_value == "":
        _LOG.warning("Couldn't get light source hours from projector. Set status to Unknown")
        attributes_to_send = {ucapi.sensor.Attributes.STATE: ucapi.sensor.States.UNKNOWN, ucapi.sensor.Attributes.VALUE: current_value, ucapi.sensor.Attributes.UNIT: "h"}
    else:
        attributes_to_send = {ucapi.sensor.Attributes.STATE: ucapi.sensor.States.ON, ucapi.sensor.Attributes.VALUE: current_value, ucapi.sensor.Attributes.UNIT: "h"}

    if stored_value == current_value:
        _LOG.debug("Light source hours have not changed since the last update. Skipping update process")
    else:
        try:
            api_update_attributes = driver.api.configured_entities.update_attributes(entity_id, attributes_to_send)
        except Exception as e:
            _LOG.error(e)
            raise Exception("Error while updating sensor value for entity id " + entity_id) from e

        if not api_update_attributes:
            raise Exception("Sensor entity " + entity_id + " not found. Please make sure it's added as a configured entity on the remote")

        _LOG.info("Updated light source timer sensor value to " + str(current_value))
