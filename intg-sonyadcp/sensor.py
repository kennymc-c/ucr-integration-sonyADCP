#!/usr/bin/env python3

"""Module that includes functions to add/remove sensor entities and to poll the sensor data"""

import logging

import ucapi

import config
import driver
import projector
import adcp as ADCP

_LOG = logging.getLogger(__name__)



async def add(device_id: str, sensor_type: str):
    """Function to add a sensor entity with the given sensor type. Will check if the sensor type is supported by the projector before adding it.
    
    :param device_id: The device ID of the projector
    :param sensor_type: The type of the sensor to add. Possible values are config.Setup["sensor_types"]
    """

    try:
        sensor_name = config.Devices.get(device_id=device_id, key="sensor-"+sensor_type+"-name")
        sensor_id = config.Devices.get(device_id=device_id, key="sensor-"+sensor_type+"-id")
        sensor_device_class = None
        sensor_attributes = {ucapi.sensor.Attributes.STATE: ucapi.sensor.States.ON}
        sensor_options = {}

        if sensor_type not in config.SensorTypes.get_all():
            _LOG.error(f"Sensor type {sensor_type} is not valid. Cannot add sensor entity for {device_id}. Valid types are {str(config.Setup.get('sensor_types'))}")
            return

        if sensor_type == config.SensorTypes.LIGHT_TIMER:
            sensor_device_class = ucapi.sensor.DeviceClasses.CUSTOM
            sensor_attributes.update({ucapi.sensor.Attributes.UNIT: "h"})
            sensor_options = {ucapi.sensor.Options.CUSTOM_UNIT: "h"}

        elif sensor_type in (config.SensorTypes.VIDEO_SIGNAL, config.SensorTypes.SYSTEM_STATUS):
            sensor_device_class = ucapi.sensor.DeviceClasses.CUSTOM

        elif sensor_type in (config.SensorTypes.POWER_STATUS, config.SensorTypes.PICTURE_MUTING, config.SensorTypes.INPUT_LAG_REDUCTION):
            sensor_device_class = ucapi.sensor.DeviceClasses.BINARY
            #TODO #WAIT Uncomment when binary sensor device classes are implemeneted
            #(https://github.com/unfoldedcircle/core-api/blob/main/doc/entities/entity_sensor.md#binary-device-class)
            #Set binary sensor device class based on Home Assistant (https://www.home-assistant.io/integrations/binary_sensor/#device-class)
            # if sensor_type == config.SensorTypes.POWER_STATUS:
            #     sensor_attributes.update({ucapi.sensor.Attributes.UNIT: "power"})

        #The remaining sensors that will only be added if the corresponding setting is supported by the projector
        else:
            if sensor_type == config.SensorTypes.TEMPERATURE:
                sensor_device_class = ucapi.sensor.DeviceClasses.TEMPERATURE
            else:
                sensor_device_class = ucapi.sensor.DeviceClasses.CUSTOM

            _LOG.debug(f"Checking if {sensor_type} is a valid setting for {device_id}")
            try:
                await projector.get_setting(device_id, setting=sensor_type)
            except NameError:
                _LOG.info(f"Setting {sensor_type} is not supported for this model. The sensor will not be added as available entity")
                return
            except OSError:
                _LOG.info(f"Could not get a value for {sensor_type}. Probably because the projector is powered off. \
The sensor will be updated when the projector is powered on")
            except Exception as e:
                error_msg = str(e)
                if error_msg:
                    _LOG.debug(e)
                _LOG.warning(f"Error while checking if setting {sensor_type} is valid for {device_id}. \
Adding sensor anyway. It will be updated when the projector is reachable")

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

    except Exception as e:
        error_msg = str(e)
        if error_msg:
            _LOG.error(f"Exception details: {e}")
        _LOG.error(f"Error while adding sensor entity {sensor_type} for device {device_id}. Sensor will not be available until integration is restarted")



async def remove(device_id: str, sensor_type: str):
    """Function to remove a sensor entity with the config sensor class definition
    
    :param device_id: The device ID of the projector
    :param sensor_type: The type of the sensor to remove. Possible values are config.Setup["sensor_types"]
    """

    if sensor_type not in config.SensorTypes.get_all():
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
        health_poller_interval = config.Devices.get(device_id=device_id, key=config.DevicesKeys.HEALTH_POLLER_INTERVAL)
        if health_poller_interval is None:
            health_poller_interval = config.Setup.get(config.Setup.Keys.DEFAULT_POLLER_INTERVAL_HEALTH)

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
        if config.Setup.get(config.Setup.Keys.STANDBY):
            continue
        try:
            projector_power = await projector.get_setting(device_id, config.SensorTypes.POWER_STATUS)
            if projector_power == ADCP.Values.States.OFF:
                _LOG.debug("Skip updating health sensors. Projector is powered off")
                continue
        except Exception as e:
            #TODO Implement check if there are too many timeouts/connection errors to the projector and automatically deactivate poller and set entity status to unknown
            _LOG.error(e)
            continue
        try:
            #TODO Add check if network and remote is reachable
            await update_setting(device_id, config.SensorTypes.LIGHT_TIMER)
            await update_system(device_id)
            if driver.api.available_entities.contains(config.Devices.get(device_id=device_id, key=f"sensor-{config.SensorTypes.TEMPERATURE}-id")):
                await update_setting(device_id, config.SensorTypes.TEMPERATURE)
            else:
                _LOG.debug(f"Skip updating temperature sensor for {device_id} as it's not an available entity")
        except Exception as e:
            _LOG.error(e)
            continue



async def update_system(device_id: str):
    """Update system status sensor. Compare retrieved messages with the last messages from the remote and update it if necessary"""

    system_id = config.Devices.get(device_id=device_id, key="sensor-system-id")

    if driver.api.configured_entities.get(system_id) is None:
        _LOG.info(f"Entity {system_id} not found in configured entities. Skip updating attributes")
        return True

    try:
        err_msg = await projector.get_setting(device_id, config.SensorSystemStatusTypes.ERROR)
        warn_msg = await projector.get_setting(device_id, config.SensorSystemStatusTypes.WARNING)
        current_value = f"{err_msg} / {warn_msg}"
    except Exception as e:
        _LOG.warning(f"Failed to get error and warning messages from {device_id}")
        _LOG.debug(e)
        current_value = config.Messages.ERROR

    current_value_prettified = config.convert_options(current_value)

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

    if current_value_prettified == config.Messages.ERROR:
        _LOG.warning(f"Couldn't get error and warning messages for {device_id}. Setting state to \"{ucapi.select.States.UNKNOWN}\"")
        attributes_to_send = {ucapi.sensor.Attributes.STATE: ucapi.sensor.States.UNKNOWN, ucapi.sensor.Attributes.VALUE: current_value_prettified}
    else:
        attributes_to_send = {ucapi.sensor.Attributes.STATE: ucapi.sensor.States.ON, ucapi.sensor.Attributes.VALUE: current_value_prettified}

    if stored_value == current_value_prettified:
        _LOG.debug(f"System status value for {device_id} has not changed since the last update. Skipping update process")
    else:
        try:
            driver.api.configured_entities.update_attributes(system_id, attributes_to_send)
        except Exception as e:
            _LOG.error(e)
            raise Exception(f"Error while updating error and warning messages for {system_id}") from e

        _LOG.info(f"Updated error and warning messages for {system_id} to {current_value_prettified}")



async def update_video(device_id: str):
    """Update video signal info sensor"""

    sensor_video_id = config.Devices.get(device_id=device_id, key="sensor-video-id")

    if driver.api.configured_entities.get(sensor_video_id) is None:
        _LOG.info(f"Entity {sensor_video_id} not found in configured entities. Skip updating attributes")
        return True

    no_signal = False
    muted = False
    state = ucapi.sensor.States.UNAVAILABLE
    video_info = ""

    _LOG.info(f"Updating video signal infos for {device_id} in video signal sensor")

    if await projector.get_setting(device_id, config.SensorTypes.PICTURE_MUTING) == ADCP.Values.States.ON.replace("\"", ""):
        muted = True

    if muted:
        _LOG.info(f"Video is muted for projector {device_id}")
        video_info = config.Messages.VIDEO_MUTED
        state = ucapi.sensor.States.ON
    else:
        try:
            resolution = await projector.get_setting(device_id, config.SensorVideoSignalTypes.RESOLUTION)
            if resolution == ADCP.Responses.States.INVALID.replace("\"", "").title(): #Compare with converted value from get_setting()
                resolution = config.Messages.NO_SIGNAL
                no_signal = True
        except Exception:
            _LOG.warning(f"Failed to get video resolution from {device_id}")
            resolution = config.Messages.ERROR

        if no_signal:
            video_info = resolution
            state = ucapi.sensor.States.ON
        else:
            try:
                dyn_range = await projector.get_setting(device_id, config.SensorVideoSignalTypes.DYNAMIC_RANGE)
            except Exception:
                _LOG.warning(f"Failed to get dynamic range from {device_id}")
                dyn_range = config.Messages.ERROR

            try:
                color_space = await projector.get_setting(device_id, config.SensorTypes.COLOR_SPACE)
            except Exception:
                _LOG.warning(f"Failed to get color space from {device_id}")
                color_space = config.Messages.ERROR

            try:
                color_format = await projector.get_setting(device_id, config.SensorVideoSignalTypes.COLOR_FORMAT)
            except Exception:
                _LOG.warning(f"Failed to get color format from {device_id}")
                color_format = config.Messages.ERROR

            try:
                mode_2d_3d = await projector.get_setting(device_id, config.SensorTypes.MODE_2D_3D)
            except Exception:
                _LOG.warning(f"Failed to get 2d/3d mode from {device_id}")
                mode_2d_3d = config.Messages.ERROR

            if any(value == config.Messages.ERROR for value in (resolution, dyn_range, color_space, color_format, mode_2d_3d)):
                _LOG.warning(f"Couldn't get (some) video infos for {device_id}. Setting sensor state to \"{ucapi.sensor.States.UNKNOWN}\"")
                state = ucapi.sensor.States.UNKNOWN
            else:
                state = ucapi.sensor.States.ON

            video_info = \
                f"{config.convert_options(resolution).lower()} / {config.convert_options(dyn_range)} / \
                {config.convert_options(color_space)} / {config.convert_options(color_format)} / {config.convert_options(mode_2d_3d)}"

    attributes_to_send = {ucapi.sensor.Attributes.STATE: state, ucapi.sensor.Attributes.VALUE: video_info}

    try:
        driver.api.configured_entities.update_attributes(sensor_video_id , attributes_to_send)
    except Exception as e:
        _LOG.error(e)
        raise Exception(f"Error while updating video signal infos for {sensor_video_id}") from e

    _LOG.info(f"Updated video signal infos for {sensor_video_id} to {video_info}")



async def update_setting(device_id: str, setting: str):
    """Function to update setting sensor entity attributes for the given setting.
    Only updates the value attribute if the value has changed since the last update to avoid unnecessary updates.

    :param device_id: The device ID of the projector
    :param setting: The name of the setting that triggered the update
    """

    if setting not in config.SensorTypes.get_all():
        if setting in config.SelectTypes.get_all():
            if setting == config.SelectTypes.POWER:
                setting = config.SensorTypes.POWER_STATUS
            if setting == config.SelectTypes.HDR_FORMAT:
                setting = config.SensorTypes.HDR_STATUS
        else:
            raise Exception(f"{setting} is not a valid sensor or select type")

    sensor_id = config.Devices.get(device_id=device_id, key="sensor-"+setting+"-id")
    current_value = ""

    _LOG.info(f"Updating {setting} setting for {sensor_id}")

    try:
        current_value = await projector.get_setting(device_id, setting)
    except OSError:
        _LOG.info(f"Could not temporarily get options for setting \"{setting}\". \
Either because the projector is powered off or the current signal doesn't support this setting or mode")
        #These are binary or temperature sensors that only accept ints or bools as values
        if not setting in (config.SensorTypes.PICTURE_MUTING, config.SensorTypes.INPUT_LAG_REDUCTION):
            _LOG.info(f"Setting state to \"{ucapi.sensor.States.UNKNOWN}\" and value to \"{config.Messages.TEMPORARILY_UNAVAILABLE}\" until options can be retrieved")
            _LOG.info("State and value for this sensor will be updated when the projector is powered on or the input is changed")
            current_value = config.Messages.TEMPORARILY_UNAVAILABLE
        else:
            _LOG.info(f"Setting state to \"{ucapi.sensor.States.UNKNOWN}\" until value can be retrieved")
            _LOG.info("State for this sensor will be updated when the projector is powered on or the input is changed")
            current_value = ""
    except Exception as e:
        #These are binary or temperature sensors that only accept ints or bools as values
        if not setting in (config.SensorTypes.TEMPERATURE, config.SensorTypes.PICTURE_MUTING, config.SensorTypes.INPUT_LAG_REDUCTION):
            _LOG.warning(f"Failed to get {setting} value from {device_id}. Setting value to \"{config.Messages.ERROR}\" and state to \"{ucapi.sensor.States.UNAVAILABLE}\"")
            _LOG.debug(e)
            current_value = config.Messages.ERROR

    state = ucapi.sensor.States.UNAVAILABLE
    if current_value in (config.Messages.ERROR, config.Messages.TEMPORARILY_UNAVAILABLE, ""):
        state = ucapi.sensor.States.UNKNOWN
    else:
        state = ucapi.sensor.States.ON

    if setting not in (config.SensorTypes.POWER_STATUS, config.SensorTypes.PICTURE_MUTING, config.SensorTypes.INPUT_LAG_REDUCTION):
        current_value_prettified = config.convert_options(current_value)
    else:
        current_value_prettified = current_value

    #Laser brightness shown in projector menu has a different scale than adcp value
    #Might also needs to be done with IRIS_BRIGHTNESS. Wait for user feedback
    if setting == config.SensorTypes.LASER_BRIGHTNESS and current_value_prettified not in (config.Messages.ERROR, config.Messages.TEMPORARILY_UNAVAILABLE):
        current_value_prettified = int(current_value_prettified)/10

    #Check if the sensor value has changed since the last update to avoid unnecessary updates due to poller tasks that run even if no setting might have been changed
    try:
        stored_states = await driver.api.available_entities.get_states()
    except Exception as e:
        raise Exception(e) from e

    if stored_states != []:
        attributes_stored = next((state["attributes"] for state in stored_states if state["entity_id"] == sensor_id),None)
    else:
        raise Exception(f"Got empty states for {sensor_id} from remote")

    if attributes_stored is None:
        _LOG.warning(f"No stored attributes found for {sensor_id}")
        stored_value = ""
    else:
        stored_value = attributes_stored.get("value", "")

    try:
        stored_value = attributes_stored["value"]
    except KeyError as e:
        _LOG.info(f"Sensor value for {sensor_id} has not been set yet")
        stored_value = ""

    if current_value_prettified == config.Messages.ERROR:
        _LOG.warning(f"Couldn't get {setting} value from {device_id}. Setting state to \"{ucapi.sensor.States.UNKNOWN}\"")
        attributes_to_send = \
        {ucapi.sensor.Attributes.STATE: ucapi.sensor.States.UNKNOWN, ucapi.sensor.Attributes.VALUE: current_value_prettified, ucapi.sensor.Attributes.UNIT: ""}
    else:
        attributes_to_send = \
        {ucapi.sensor.Attributes.STATE: ucapi.sensor.States.ON, ucapi.sensor.Attributes.VALUE: current_value_prettified, ucapi.sensor.Attributes.UNIT: "h"}

    if stored_value == current_value_prettified:
        _LOG.debug(f"Sensor value for {sensor_id} has not changed since the last update. Skipping update process")
    else:
        attributes_to_send = {ucapi.sensor.Attributes.STATE: state, ucapi.sensor.Attributes.VALUE: current_value_prettified}

        try:
            driver.api.configured_entities.update_attributes(sensor_id, attributes_to_send)
        except Exception as e:
            _LOG.error(e)
            raise Exception(f"Error while updating sensor value for {sensor_id}") from e

        _LOG.info(f"Updated {setting} for {sensor_id} sensor value to " + str(current_value_prettified))



async def update_all_sensors(device_id:str):
    """Update all sensor entity value attributes for a specific device"""
    for sensor_type in config.SensorTypes.get_all():

        if sensor_type not in [config.SensorTypes.VIDEO_SIGNAL, config.SensorTypes.SYSTEM_STATUS]:
            sensor_id = f"sensor-{sensor_type}-{device_id}"
            if driver.api.available_entities.contains(sensor_id):
                try:
                    await update_setting(device_id, sensor_type)
                except Exception as e:
                    error_msg = str(e)
                    if error_msg:
                        _LOG.warning(f"Failed to update {sensor_type} sensor value for {device_id}")
                        _LOG.warning(error_msg)
                    else:
                        _LOG.warning(f"Failed to update {sensor_type} sensor value for {device_id}")
            else:
                _LOG.debug(f"{sensor_id} is not an available entity. Skip updating attributes")

        if sensor_type is config.SensorTypes.VIDEO_SIGNAL:
            try:
                await update_video(device_id)
            except Exception as e:
                error_msg = str(e)
                if error_msg:
                    _LOG.warning(f"Failed to update video sensor sensor value for {device_id}")
                    _LOG.warning(error_msg)
                else:
                    _LOG.warning(f"Failed to update video sensor sensor value for {device_id}")

        if sensor_type is config.SensorTypes.SYSTEM_STATUS:
            try:
                await update_video(device_id)
            except Exception as e:
                error_msg = str(e)
                if error_msg:
                    _LOG.warning(f"Failed to update video sensor sensor value for {device_id}")
                    _LOG.warning(error_msg)
                else:
                    _LOG.warning(f"Failed to update video sensor sensor value for {device_id}")
