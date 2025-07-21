#!/usr/bin/env python3

"""Module that includes functions to add a light source timer sensor entity and to poll the sensor data"""

import logging

import ucapi

import config
import driver
import projector

_LOG = logging.getLogger(__name__)


#TODO Combine all sensor add and remove functions into 2 function that take the device_id and sensor type as parameters
async def add_light_sensor(device_id: str):
    """Function to add a light source timer sensor entity with the config.LSTSensor class definition and get current light source hours"""

    lt_name = config.Devices.get(device_id=device_id, key="lt-name")
    lt_id = config.Devices.get(device_id=device_id, key="lt-id")

    definition = config.LSTSensor().get_def(ent_id=lt_id, name=lt_name)

    driver.api.available_entities.add(definition)

    _LOG.info(f"Added projector light source timer sensor entity with id {lt_id} and name {lt_name} as available entity")



async def remove_light_sensor(device_id: str):
    """Function to remove a light source timer sensor entity with the config.LSTSensor class definition and get current light source hours"""

    lt_name = config.Devices.get(device_id=device_id, key="lt-name")
    lt_id = config.Devices.get(device_id=device_id, key="lt-id")

    definition = config.LSTSensor().get_def(ent_id=lt_id, name=lt_name)

    driver.api.available_entities.add(definition)

    _LOG.info(f"Removed projector light source timer sensor entity with id {lt_id} and name {lt_name} as available entity")



async def add_video_sensor(device_id: str):
    """Function to add a video info sensor entity with the config.VISensor class definition and get current video signal info"""

    vi_name = config.Devices.get(device_id=device_id, key="sensor-video-name")
    vi_id = config.Devices.get(device_id=device_id, key="sensor-video-id")

    definition = config.VISensor().get_def(ent_id=vi_id, name=vi_name)

    driver.api.available_entities.add(definition)

    _LOG.info(f"Added projector video info sensor entity with id {vi_id} and name {vi_name} as available entity")



async def remove_video_sensor(device_id: str):
    """Function to remove a video info sensor entity with the config.VISensor class definition and get current video signal info"""

    vi_name = config.Devices.get(device_id=device_id, key="sensor-video-name")
    vi_id = config.Devices.get(device_id=device_id, key="sensor-video-id")

    definition = config.VISensor().get_def(ent_id=vi_id, name=vi_name)

    driver.api.available_entities.add(definition)

    _LOG.info(f"Removed projector video info sensor entity with id {vi_id} and name {vi_name} as available entity")



async def add_temp_sensor(device_id: str):
    """Function to add a temperature sensor entity with the config.TEMPSensor class definition and get current projector temperature"""

    temp_name = config.Devices.get(device_id=device_id, key="sensor-temp-name")
    temp_id = config.Devices.get(device_id=device_id, key="sensor-temp-id")

    definition = config.TEMPSensor().get_def(ent_id=temp_id, name=temp_name)

    driver.api.available_entities.add(definition)

    _LOG.info(f"Added projector temperature sensor entity with id {temp_id} and name {temp_name} as available entity")



async def remove_temp_sensor(device_id: str):
    """Function to remove a temperature sensor entity with the config.TEMPSensor class definition and get current projector temperature"""

    temp_name = config.Devices.get(device_id=device_id, key="sensor-temp-name")
    temp_id = config.Devices.get(device_id=device_id, key="sensor-temp-id")

    definition = config.TEMPSensor().get_def(ent_id=temp_id, name=temp_name)

    driver.api.available_entities.add(definition)

    _LOG.info(f"Removed projector temperature sensor entity with id {temp_id} and name {temp_name} as available entity")



async def add_system_sensor(device_id: str):
    """Function to add a system status sensor entity with the config.SYSTEMSensor class definition and get current error and warning messages"""

    system_name = config.Devices.get(device_id=device_id, key="sensor-system-name")
    system_id = config.Devices.get(device_id=device_id, key="sensor-system-id")

    definition = config.SYSTEMSensor().get_def(ent_id=system_id, name=system_name)

    driver.api.available_entities.add(definition)

    _LOG.info(f"Added projector system status sensor entity with id {system_id} and name {system_name} as available entity")



async def remove_system_sensor(device_id: str):
    """Function to remove a system status sensor entity with the config.SYSTEMSensor class definition and get current error and warning messages"""

    system_name = config.Devices.get(device_id=device_id, key="sensor-system-name")
    system_id = config.Devices.get(device_id=device_id, key="sensor-system-id")

    definition = config.SYSTEMSensor().get_def(ent_id=system_id, name=system_name)

    driver.api.available_entities.add(definition)

    _LOG.info(f"Removed projector system status sensor entity with id {system_id} and name {system_name} as available entity")



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

    lt_id = config.Devices.get(device_id=device_id, key="lt-id")

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
        attributes_stored = stored_states[1]["attributes"] # [1] = 2nd entity that has been added
    else:
        raise Exception(f"Got empty states for {device_id} from remote. Please make sure to add configured entities")

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
            api_update_attributes = driver.api.configured_entities.update_attributes(lt_id, attributes_to_send)
        except Exception as e:
            _LOG.error(e)
            raise Exception("Error while updating sensor value for entity id " + lt_id) from e

        if not api_update_attributes:
            raise Exception("Sensor entity " + lt_id + " not found. Please make sure it's added as a configured entity on the remote")

        _LOG.info(f"Updated light source timer for {device_id} sensor value to " + str(current_value))



async def update_temp(device_id: str):
    """Update projector temperature sensor. Compare retrieved temperature with the last sensor value from the remote and update it if necessary"""

    temp_id = config.Devices.get(device_id=device_id, key="sensor-temp-id")
    state = ucapi.sensor.States.UNAVAILABLE

    try:
        current_value = await projector.get_temp(device_id)
    except OSError as o:
        _LOG.info(o)
        _LOG.info("Retuning N/A as value")
        current_value = "N/A"
        _LOG.info("Set state to Unknown")
        state = ucapi.sensor.States.UNKNOWN #Better than unavailable as the UI shows the sensor as off wth an unknown state
    except NameError as n:
        _LOG.info(n)
        _LOG.info("Retuning N/A as value")
        current_value = "N/A"
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
        attributes_stored = stored_states[2]["attributes"] # [2] = 3rd entity that has been added
    else:
        raise Exception(f"Got empty states for {device_id} from remote. Please make sure to add configured entities")

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
            api_update_attributes = driver.api.configured_entities.update_attributes(temp_id, attributes_to_send)
        except Exception as e:
            _LOG.error(e)
            raise Exception("Error while updating sensor value for entity id " + temp_id) from e

        if not api_update_attributes:
            raise Exception("Sensor entity " + temp_id + " not found. Please make sure it's added as a configured entity on the remote")

        _LOG.info(f"Updated temperature value for {device_id} sensor value to " + str(current_value))



async def update_system(device_id: str):
    """Update system status sensor. Compare retrieved messages with the last messages from the remote and update it if necessary"""

    system_id = config.Devices.get(device_id=device_id, key="sensor-system-id")

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
        attributes_stored = stored_states[3]["attributes"] # [3] = 4th entity that has been added
    else:
        raise Exception(f"Got empty states for {device_id} from remote. Please make sure to add configured entities")

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
            api_update_attributes = driver.api.configured_entities.update_attributes(system_id, attributes_to_send)
        except Exception as e:
            _LOG.error(e)
            raise Exception("Error while updating sensor value for entity id " + system_id) from e

        if not api_update_attributes:
            raise Exception("Sensor entity " + system_id + " not found. Please make sure it's added as a configured entity on the remote")

        _LOG.info(f"Updated error and warning messages for {device_id} sensor value to " + str(current_value))



async def update_video(device_id: str):
    """Update video info sensor"""

    sensor_video_id = config.Devices.get(device_id=device_id, key="sensor-video-id")
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
        except Exception as e:
            _LOG.warning(f"Failed to get video resolution from {device_id}")
            resolution = "Error"
            raise Exception(e) from e

        if no_signal:
            video_info = resolution
            state = ucapi.sensor.States.UNKNOWN #Better than unavailable as the UI shows the sensor as off wth an unknown state
        else:
            try:
                dyn_range = await projector.get_dynamic_range(device_id)
            except Exception as e:
                _LOG.warning(f"Failed to get color space from {device_id}")
                dyn_range = "Error"
                raise Exception(e) from e

            try:
                color_space = await projector.get_color_space(device_id)
            except Exception as e:
                _LOG.warning(f"Failed to get color space from {device_id}")
                color_space = "Error"
                raise Exception(e) from e

            try:
                color_format = await projector.get_color_format(device_id)
            except Exception as e:
                _LOG.warning(f"Failed to get color format from {device_id}")
                color_format = "Error"
                raise Exception(e) from e

            try:
                mode_2d_3d = await projector.get_mode_2d_3d(device_id)
            except Exception as e:
                _LOG.warning(f"Failed to get 2d/3d mode from {device_id}")
                mode_2d_3d = "Error"
                raise Exception(e) from e

            if resolution == "Error" or dyn_range == "Error" or color_space == "Error" or color_format == "Error" or mode_2d_3d == "Error":
                _LOG.warning(f"Couldn't get (some) video infos for {device_id}. Set sensor state to Unknown")
                state = ucapi.sensor.States.UNKNOWN
            else:
                state = ucapi.sensor.States.ON

            video_info = f"{resolution} / {dyn_range} / {color_space} / {color_format} / {mode_2d_3d}"

    attributes_to_send = {ucapi.sensor.Attributes.STATE: state, ucapi.sensor.Attributes.VALUE: video_info}

    try:
        api_update_attributes = driver.api.configured_entities.update_attributes(sensor_video_id , attributes_to_send)
    except Exception as e:
        _LOG.error(e)
        raise Exception("Error while updating sensor value for entity id " + sensor_video_id ) from e

    if not api_update_attributes:
        raise Exception("Sensor entity " + sensor_video_id  + " not found. Please make sure it's added as a configured entity on the remote")

    _LOG.info(f"Updated video signal infos for {device_id} sensor value to " + str(video_info))
