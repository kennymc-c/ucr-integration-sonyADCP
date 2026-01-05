#!/usr/bin/env python3

"""Module that includes functions to add a light source timer sensor entity and to poll the sensor data"""

import logging

import ucapi

import config
import driver
import projector

_LOG = logging.getLogger(__name__)


#TODO Add settings sensors (e.g. picture mode, hdr mode, gamma etc.).
# If a setting gets changed a global update settings sensor function is called. If theres a sensor for that setting it will be updated with the new value.



async def add(device_id: str, sensor_type: str):
    """Function to add a sensor entity with the given sensor type. Will check if the sensor type is supported by the projector before adding it.
    
    :param device_id: The device ID of the projector
    :param sensor_type: The type of the sensor to add. Possible values are config.Setup["sensor_types"]
    """

    sensor_name = config.Devices.get(device_id=device_id, key="sensor-"+sensor_type+"-name")
    sensor_id = config.Devices.get(device_id=device_id, key="sensor-"+sensor_type+"-id")
    sensor_device_class = None
    sensor_attributes = {ucapi.sensor.Attributes.STATE: ucapi.sensor.States.ON}
    sensor_options = {}

    if sensor_type not in config.Setup.get("sensor_types"):
        _LOG.error(f"Sensor type {sensor_type} is not valid. Cannot add sensor entity for {device_id}. Valid types are {str(config.Setup.get('sensor_types'))}")
        return

    if sensor_type == "light":
        sensor_device_class = ucapi.sensor.DeviceClasses.CUSTOM
        sensor_attributes.update({ucapi.sensor.Attributes.UNIT: "h"})
        sensor_options = {ucapi.sensor.Options.CUSTOM_UNIT: "h"}

    elif sensor_type == "temp":
        _LOG.debug(f"Checking if temperature sensor is supported for {device_id}")
        try:
            await projector.get_temp(device_id)
        except NameError:
            _LOG.info("Temperature sensor will not be added as available entity as it's not supported by the projector model")
            return
        sensor_device_class = ucapi.sensor.DeviceClasses.TEMPERATURE

    elif sensor_type in ("video", "system"):
        sensor_device_class = ucapi.sensor.DeviceClasses.CUSTOM

    elif sensor_type in ("picture-muting", "input-lag-reduction"):
        sensor_device_class = ucapi.sensor.DeviceClasses.BINARY
        sensor_attributes.update({ucapi.sensor.Attributes.UNIT: sensor_type.replace("-"," ").title()})

    else:
        sensor_device_class = ucapi.sensor.DeviceClasses.CUSTOM
        _LOG.debug(f"Checking if {sensor_type} is a valid setting for {device_id}")
        try:
            await projector.get_setting(device_id, setting=sensor_type)
        except NameError:
            _LOG.info(f"Setting {sensor_type} is not supported for this model. The sensor will not be added as available entity")
            return
        except OSError:
            _LOG.info(f"Could not get a value for {sensor_type}. Probably because the projector is powered off. The sensor will be updated when the projector is powered on")
        except Exception as e:
            error_msg = str(e)
            if error_msg:
                _LOG.debug(e)
            _LOG.error(f"Error while checking if setting {sensor_type} is valid for {device_id}. Trying later when the projector is powered on")

    definition = ucapi.Sensor(
        sensor_id,
        sensor_name,
        features=None, #Mandatory although sensor entities have no features
        attributes=sensor_attributes,
        device_class=sensor_device_class,
        options=sensor_options,
    )

    driver.api.available_entities.add(definition)

    _LOG.info(f"Added projector sensor entity with id {sensor_id} and name {sensor_name} as available entity")



async def remove(device_id: str, sensor_type: str):
    """Function to remove a sensor entity with the config sensor class definition
    
    :param device_id: The device ID of the projector
    :param sensor_type: The type of the sensor to remove. Possible values are config.Setup["sensor_types"]
    """

    if sensor_type not in config.Setup.get("sensor_types"):
        _LOG.error(f"Sensor type {sensor_type} is not valid. Cannot remove sensor entity for device_id {device_id}. Valid types are {str(config.Setup.get('sensor_types'))}")
        return

    sensor_id = config.Devices.get(device_id=device_id, key="sensor-"+sensor_type+"-id")
    sensor_name = config.Devices.get(device_id=device_id, key="sensor-"+sensor_type+"-name")

    driver.api.available_entities.remove(sensor_id)

    _LOG.info(f"Removed projector sensor entity with id {sensor_id} and name {sensor_name} as available entity")



class HealthPollerController():
    """(Re)Starts or stops a task to regularly poll health data from the projector"""

    @staticmethod
    async def start(device_id: str):
        """Starts the health_poller task. If the task is already running it will be stopped and restarted"""

        name = device_id + "-health_poller"
        health_poller_interval = config.Devices.get(device_id=device_id, key="health_poller_interval")
        if health_poller_interval is None:
            health_poller_interval = config.Setup.get("default_health_poller_interval")

        if health_poller_interval == 0:
            _LOG.debug("Health poller interval set to " + str(health_poller_interval))
            try:
                poller_task, = [task for task in driver.asyncio.all_tasks() if task.get_name() == name]
                poller_task.cancel()
                try:
                    await poller_task
                except driver.asyncio.CancelledError:
                    _LOG.info(f"Stopped running health poller task \"{name}\"")
            except ValueError:
                _LOG.info(f"The health poller task for device_id \"{device_id}\" will not be started")
        else:
            try:
                poller_task, = [task for task in driver.asyncio.all_tasks() if task.get_name() == name]
                poller_task.cancel()
                try:
                    await poller_task
                except driver.asyncio.CancelledError:
                    driver.loop.create_task(health_poller(device_id, health_poller_interval), name=name)
                    _LOG.info(f"Restarted health poller task \"{name}\" with an interval of {str(health_poller_interval)} seconds")
            except ValueError:
                driver.loop.create_task(health_poller(device_id, health_poller_interval), name=name)
                _LOG.info(f"Started health poller task \"{name}\" with an interval of {str(health_poller_interval)} seconds")

    @staticmethod
    async def stop(device_id:str = None):
        """Stops the health_poller task for the given device_id"""

        async def stop_task(name):
            try:
                poller_task, = [task for task in driver.asyncio.all_tasks() if task.get_name() == name]
                poller_task.cancel()
                try:
                    await poller_task
                except driver.asyncio.CancelledError:
                    _LOG.debug(f"Stopped health poller task \"{name}\"")
            except ValueError:
                if device_id is not None:
                    _LOG.debug(f"There is no running health poller task named \"{name}\"")

        if device_id is None:
            _LOG.debug("No device_id provided. Stopping all health poller tasks")
            for device in config.Devices.list():
                name = str(device) + "-health_poller"
                await stop_task(name)
        else:
            name = device_id + "-health_poller"
            await stop_task(name)



async def health_poller(device_id: str, interval:int) -> None:
    """Projector health poller task. Runs only when the projector is powered on"""
    while True:
        await driver.asyncio.sleep(interval)
        if config.Setup.get("standby"):
            continue
        try:
            projector_power = await projector.get_attr_power(device_id)
            if projector_power == {ucapi.media_player.Attributes.STATE: ucapi.media_player.States.OFF}:
                _LOG.debug("Skip updating health sensors. Projector is powered off")
                continue
        except Exception as e:
            #TODO Implement check if there are too many timeouts/connection errors to the projector and automatically deactivate poller and set entity status to unknown
            _LOG.error(e)
            continue
        try:
            #TODO Add check if network and remote is reachable
            await update_light(device_id)
            await update_system(device_id)
            if driver.api.available_entities.contains(config.Devices.get(device_id=device_id, key="sensor-temp-id")):
                await update_temp(device_id)
            else:
                _LOG.debug(f"Skip updating temperature sensor for {device_id} as it's not an available entity")
        except Exception as e:
            _LOG.error(e)
            continue



async def update_light(device_id: str):
    """Update light source timer sensor. Compare retrieved light source hours with the last sensor value from the remote and update it if necessary"""

    light_id = config.Devices.get(device_id=device_id, key="sensor-light-id")

    if driver.api.configured_entities.get(light_id) is None:
        _LOG.info(f"Entity {light_id} not found in configured entities. Skip updating attributes")
        return True

    try:
        current_value = await projector.get_light_source_hours(device_id)
    except Exception as e:
        _LOG.warning(f"Failed to get light source hours from {device_id}. Use empty sensor value")
        _LOG.debug(e)
        current_value = "Error"

    try:
        stored_states = await driver.api.available_entities.get_states()
    except Exception as e:
        raise Exception(e) from e

    if stored_states != []:
        attributes_stored = next((state["attributes"] for state in stored_states if state["entity_id"] == light_id),None)
    else:
        raise Exception(f"Got empty states for {device_id} from remote")

    try:
        stored_value = attributes_stored["value"]
    except KeyError as e:
        _LOG.info(f"Light source timer sensor value for {device_id} has not been set yet")
        stored_value = ""

    if current_value == "Error":
        _LOG.warning(f"Couldn't get light source hours for {device_id}. Set status to Unknown")
        attributes_to_send = {ucapi.sensor.Attributes.STATE: ucapi.sensor.States.UNKNOWN, ucapi.sensor.Attributes.VALUE: current_value, ucapi.sensor.Attributes.UNIT: ""}
    else:
        attributes_to_send = {ucapi.sensor.Attributes.STATE: ucapi.sensor.States.ON, ucapi.sensor.Attributes.VALUE: current_value, ucapi.sensor.Attributes.UNIT: "h"}

    if stored_value == current_value:
        _LOG.debug(f"Light source hours for {device_id} have not changed since the last update. Skipping update process")
    else:
        try:
            driver.api.configured_entities.update_attributes(light_id, attributes_to_send)
        except Exception as e:
            _LOG.error(e)
            raise Exception("Error while updating sensor value for entity id " + light_id) from e

        _LOG.info(f"Updated light source timer for {device_id} sensor value to " + str(current_value))



async def update_temp(device_id: str):
    """Update projector temperature sensor. Compare retrieved temperature with the last sensor value from the remote and update it if necessary"""

    temp_id = config.Devices.get(device_id=device_id, key="sensor-temp-id")

    if driver.api.configured_entities.get(temp_id) is None:
        _LOG.info(f"Entity {temp_id} not found in configured entities. Skip updating attributes")
        return True

    state = ucapi.sensor.States.UNAVAILABLE

    current_value = "N/A"
    try:
        current_value = await projector.get_temp(device_id)
    except OSError as o:
        _LOG.info(o)
        _LOG.info("Set state to Unknown")
        state = ucapi.sensor.States.UNKNOWN #Better than unavailable as the UI shows the sensor as off wth an unknown state
    except NameError as n:
        _LOG.info(n)
        _LOG.info("Set state to Unknown")
        state = ucapi.sensor.States.UNKNOWN #Better than unavailable as the UI shows the sensor as off wth an unknown state
    except Exception as e:
        _LOG.warning(f"Failed to get temperature from {device_id}. Use ??? as sensor value")
        _LOG.debug(e)
        current_value = "Error"

    try:
        stored_states = await driver.api.available_entities.get_states()
    except Exception as e:
        raise Exception(e) from e

    if stored_states != []:
        attributes_stored = next((state["attributes"] for state in stored_states if state["entity_id"] == temp_id),None)
    else:
        raise Exception(f"Got empty states for {device_id} from remote")

    try:
        stored_value = attributes_stored["value"]
    except KeyError as e:
        _LOG.info(f"Temperature sensor value for {device_id} has not been set yet")
        stored_value = ""

    if current_value == "Error":
        _LOG.warning(f"Couldn't get temperature value for {device_id}. Set state to Unknown")
        state = ucapi.sensor.States.UNKNOWN
    else:
        state = ucapi.sensor.States.ON

    attributes_to_send = {ucapi.sensor.Attributes.STATE: state, ucapi.sensor.Attributes.VALUE: current_value}

    if stored_value == current_value:
        _LOG.debug(f"Temperature value for {device_id} has not changed since the last update. Skipping update process")
    else:
        try:
            driver.api.configured_entities.update_attributes(temp_id, attributes_to_send)
        except Exception as e:
            _LOG.error(e)
            raise Exception("Error while updating sensor value for entity id " + temp_id) from e

        _LOG.info(f"Updated temperature value for {device_id} sensor value to " + str(current_value))



async def update_system(device_id: str):
    """Update system status sensor. Compare retrieved messages with the last messages from the remote and update it if necessary"""

    system_id = config.Devices.get(device_id=device_id, key="sensor-system-id")

    if driver.api.configured_entities.get(system_id) is None:
        _LOG.info(f"Entity {system_id} not found in configured entities. Skip updating attributes")
        return True

    try:
        err_msg = await projector.get_error(device_id)
        warn_msg = await projector.get_warning(device_id)
        current_value = f"{err_msg} / {warn_msg}"
    except Exception as e:
        _LOG.warning(f"Failed to get error and warning messages from {device_id}")
        _LOG.debug(e)
        current_value = "Error"

    try:
        stored_states = await driver.api.available_entities.get_states()
    except Exception as e:
        raise Exception(e) from e

    if stored_states != []:
        attributes_stored = next((state["attributes"] for state in stored_states if state["entity_id"] == system_id),None)
    else:
        raise Exception(f"Got empty states for {device_id} from remote")

    try:
        stored_value = attributes_stored["value"]
    except KeyError as e:
        _LOG.info(f"Error and warning messages for {device_id} have not been set yet")
        stored_value = ""

    if current_value == "Error":
        _LOG.warning(f"Couldn't get error and warning messages for {device_id}. Set status to Unknown")
        attributes_to_send = {ucapi.sensor.Attributes.STATE: ucapi.sensor.States.UNKNOWN, ucapi.sensor.Attributes.VALUE: current_value}
    else:
        attributes_to_send = {ucapi.sensor.Attributes.STATE: ucapi.sensor.States.ON, ucapi.sensor.Attributes.VALUE: current_value}

    if stored_value == current_value:
        _LOG.debug(f"Temperature value for {device_id} has not changed since the last update. Skipping update process")
    else:
        try:
            driver.api.configured_entities.update_attributes(system_id, attributes_to_send)
        except Exception as e:
            _LOG.error(e)
            raise Exception("Error while updating sensor value for entity id " + system_id) from e

        _LOG.info(f"Updated error and warning messages for {device_id} sensor value to " + str(current_value))



async def update_video(device_id: str):
    """Update video info sensor"""

    sensor_video_id = config.Devices.get(device_id=device_id, key="sensor-video-id")

    if driver.api.configured_entities.get(sensor_video_id) is None:
        _LOG.info(f"Entity {sensor_video_id} not found in configured entities. Skip updating attributes")
        return True

    no_signal = False
    muted = False
    state = ucapi.sensor.States.UNAVAILABLE
    video_info = ""

    _LOG.info(f"Updating video signal infos for {device_id} in video signal sensor")

    if await projector.get_attr_muted(device_id):
        muted = True

    if muted:
        _LOG.info(f"Video is muted for projector {device_id}")
        video_info = "Video muted"
        state = ucapi.sensor.States.UNKNOWN #Better than unavailable as the UI shows the sensor as off wth an unknown state
    else:
        try:
            resolution = await projector.get_resolution(device_id)
            if resolution == "Invalid":
                resolution = "No signal"
                no_signal = True
        except Exception:
            _LOG.warning(f"Failed to get video resolution from {device_id}")
            resolution = "Error"

        if no_signal:
            video_info = resolution
            state = ucapi.sensor.States.UNKNOWN #Better than unavailable as the UI shows the sensor as off wth an unknown state
        else:
            try:
                dyn_range = await projector.get_dynamic_range(device_id)
            except Exception:
                _LOG.warning(f"Failed to get dynamic range from {device_id}")
                dyn_range = "Error"

            try:
                color_space = await projector.get_color_space(device_id)
            except Exception:
                _LOG.warning(f"Failed to get color space from {device_id}")
                color_space = "Error"

            try:
                color_format = await projector.get_color_format(device_id)
            except Exception:
                _LOG.warning(f"Failed to get color format from {device_id}")
                color_format = "Error"

            try:
                mode_2d_3d = await projector.get_mode_2d_3d(device_id)
            except Exception:
                _LOG.warning(f"Failed to get 2d/3d mode from {device_id}")
                mode_2d_3d = "Error"

            if resolution == "Error" or dyn_range == "Error" or color_space == "Error" or color_format == "Error" or mode_2d_3d == "Error":
                _LOG.warning(f"Couldn't get (some) video infos for {device_id}. Set sensor state to Unknown")
                state = ucapi.sensor.States.UNKNOWN
            else:
                state = ucapi.sensor.States.ON

            video_info = f"{resolution} / {dyn_range} / {color_space} / {color_format} / {mode_2d_3d}"

    attributes_to_send = {ucapi.sensor.Attributes.STATE: state, ucapi.sensor.Attributes.VALUE: video_info}

    try:
        driver.api.configured_entities.update_attributes(sensor_video_id , attributes_to_send)
    except Exception as e:
        _LOG.error(e)
        raise Exception("Error while updating sensor value for entity id " + sensor_video_id ) from e

    _LOG.info(f"Updated video signal infos for {device_id} sensor value to " + str(video_info))



async def update_setting(device_id: str, setting: str):
    """Function to update a setting sensor entity for the given setting
    
    :param device_id: The device ID of the projector
    :param setting: The name of the setting that triggered the update
    """

    _LOG.info(f"Updating {setting} sensor for {device_id}")

    try:
        current_value = await projector.get_setting(device_id, setting)
    except OSError:
        _LOG.info(f"Retrieving {setting} from {device_id} temporarily unavailable. Setting state and value to Unknown")
        current_value = "Temporarily unavailable"
    except Exception as e:
        _LOG.warning(f"Failed to get {setting} value from {device_id}. Setting value to Error and state to Unavailable")
        _LOG.debug(e)
        current_value = "Error"

    state = ucapi.sensor.States.UNAVAILABLE
    if current_value in ("Error", "Temporarily unavailable"):
        state = ucapi.sensor.States.UNKNOWN
    else:
        state = ucapi.sensor.States.ON

    if current_value == "1.85_1":
        current_value = "1.85:1"
    elif current_value == "2.35_1":
        current_value = "2.35:1"
    elif current_value == "sim3d":
        current_value = "Simulated 3D"
    elif current_value == "sidebyside":
        current_value = "Side by Side"
    elif current_value == "overunder":
        current_value = "Over Under"
    else:
        current_value = current_value.replace("_", " ").replace("brt", "bright").title()
        # If the value ends with a single digit (e.g. "Mode1"), separate it with a space -> "Mode 1"
        if len(current_value) >= 2 and current_value[-1].isdigit() and not current_value[-2].isdigit():
            current_value = current_value[:-1] + " " + current_value[-1]

    attributes_to_send = {ucapi.sensor.Attributes.STATE: state, ucapi.sensor.Attributes.VALUE: current_value}

    sensor_id = config.Devices.get(device_id=device_id, key="sensor-"+setting+"-id")
    try:
        driver.api.configured_entities.update_attributes(sensor_id, attributes_to_send)
    except Exception as e:
        _LOG.error(e)
        raise Exception("Error while updating sensor value for entity id " + sensor_id) from e

    _LOG.info(f"Updated {setting} value for {device_id} sensor value to " + str(current_value))
