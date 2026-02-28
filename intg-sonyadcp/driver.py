#!/usr/bin/env python3

"""Main driver file. Run this module to start the integration driver"""

import sys
import os
import asyncio
import logging

import ucapi

import config
import setup
import media_player
import remote
import sensor
import selects


_LOG = logging.getLogger("driver")  # avoid having __main__ in log messages

loop = asyncio.get_event_loop()
api = ucapi.IntegrationAPI(loop)


async def add_available_entities():
    """
    Called at the start of the integration driver to add all supported available entities (by remote and/or projector model)
    """
    for device_id in config.Devices.list():
        try:
            mp_entity_id = device_id
            rt_entity_id = config.Devices.get(device_id=device_id, key="remote-id")
        except ValueError as v:
            _LOG.error(v)
            continue

        #Add all entities as available entities
        if api.available_entities.contains(mp_entity_id):
            _LOG.debug("Projector media player entity with id " + mp_entity_id + " is already in storage as available entity")
        else:
            await media_player.add(device_id)

        if api.available_entities.contains(rt_entity_id):
            _LOG.debug("Projector remote entity with id " + rt_entity_id + " is already in storage as available entity")
        else:
            await remote.add(device_id)

        for sensor_type in config.SensorTypes.get_all():
            try:
                sensor_entity_id = config.Devices.get(device_id=device_id, key=f"sensor-{sensor_type}-id")
            except ValueError as v:
                _LOG.error(f"Error while getting sensor ID for {sensor_type}: {v}")
                continue

            if api.available_entities.contains(sensor_entity_id):
                _LOG.debug(f"Projector {sensor_type} sensor entity with id " + sensor_entity_id + " is already in storage as available entity")
            else:
                await sensor.add(device_id, sensor_type)

        for select_type in config.SelectTypes.get_all():
            await selects.add(device_id, select_type)



@api.listens_to(ucapi.Events.CONNECT)
async def on_intg_connect() -> None:
    """
    Connect notification from Remote.

    Just reply with connected as there is no permanent connection to the projector that needs to be re-established
    """
    _LOG.info("Received connect event message from remote")

    await api.set_device_state(ucapi.DeviceStates.CONNECTED)



@api.listens_to(ucapi.Events.DISCONNECT)
async def on_intg_disconnect() -> None:
    """
    Disconnect notification from Remote.

    Just reply with disconnected as there is no permanent connection to the projector that needs to be closed
    """
    _LOG.info("Received disconnect event message from remote")

    await api.set_device_state(ucapi.DeviceStates.DISCONNECTED)



@api.listens_to(ucapi.Events.CLIENT_CONNECTED)
async def on_client_connect() -> None:
    """
    Websocket client connect notification from Remote.
    """
    _LOG.debug("Remote websocket client connected to this integration websockets server")
    _LOG.debug("There are currently %d websocket clients connected to this integration websockets server", int(api.client_count))



@api.listens_to(ucapi.Events.CLIENT_DISCONNECTED)
async def on_client_disconnect() -> None:
    """
    Websocket client disconnect notification from the Remote.
    """
    _LOG.debug("Remote websocket client disconnected from this integration websockets server")
    client_count = int(api.client_count)
    if client_count > 0:
        _LOG.debug("There are currently %d websocket clients connected to this integration websockets server", client_count)
    else:
        _LOG.debug("No other websocket clients are currently connected to this integration websockets server")



@api.listens_to(ucapi.Events.ENTER_STANDBY)
async def on_r2_enter_standby() -> None:
    """
    Enter standby notification from Remote.

    Set standby to True and show a debug log message as there is no permanent connection to the projector that needs to be closed.
    """
    _LOG.info("Received enter standby event message from remote")

    config.Setup.set(config.Setup.Keys.STANDBY, True)



@api.listens_to(ucapi.Events.EXIT_STANDBY)
async def on_r2_exit_standby() -> None:
    """
    Exit standby notification from Remote.

    Set standby to False show and a debug log message as there is no permanent connection to the projector that needs to be re-established.
    """
    _LOG.info("Received exit standby event message from remote")

    config.Setup.set(config.Setup.Keys.STANDBY, False)



@api.listens_to(ucapi.Events.SUBSCRIBE_ENTITIES)
async def on_subscribe_entities(entity_ids: list[str]) -> None:
    """
    Subscribe to given entities.

    :param entity_ids: entity identifiers.
    """
    _LOG.info("Received subscribe entities event for entity ids: " + str(entity_ids))

    config.Setup.set(config.Setup.Keys.STANDBY, False)

    if config.Setup.get(config.Setup.Keys.SETUP_COMPLETE):
        device_ids = []

        for entity_id in entity_ids:
            # First, check if entity_id is directly a device_id (media player entity)
            if entity_id in config.Devices.list():
                device_ids.append(entity_id)
            else:
                # Try to extract device_id from entity_id (for sensor, remote, select entities)
                extracted_device_id = config.Devices.extract_device_id_from_entity_id(entity_id)
                if extracted_device_id and extracted_device_id not in device_ids:
                    device_ids.append(extracted_device_id)

        if not device_ids:
            _LOG.info("No valid device ids found in entity ids list from entity subscribe message")

        else:
            try:
                for device_id in device_ids:

                    media_player_id = config.Devices.get(device_id=device_id, key=config.DevicesKeys.DEVICE_ID)
                    remote_id = config.Devices.get(device_id=device_id, key="remote-id")
                    sensor_video_id = config.Devices.get(device_id=device_id, key=f"sensor-{config.SensorTypes.VIDEO_SIGNAL}-id")
                    sensor_system_id = config.Devices.get(device_id=device_id, key=f"sensor-{config.SensorTypes.SYSTEM_STATUS}-id")
                    sensor_light_id = config.Devices.get(device_id=device_id, key=f"sensor-{config.SensorTypes.LIGHT_TIMER}-id")
                    sensor_temp_id = config.Devices.get(device_id=device_id, key=f"sensor-{config.SensorTypes.TEMPERATURE}-id")

                    if media_player_id in entity_ids:
                        await media_player.update_attributes(device_id)
                        await media_player.MpPollerController.start(device_id)

                    if remote_id in entity_ids:
                        await remote.update_attributes(device_id)

                    if sensor_video_id in entity_ids:
                        await sensor.update_video(device_id)

                    if sensor_system_id in entity_ids:
                        await sensor.update_system(device_id)

                    if any(entity_id in (sensor_light_id, sensor_temp_id, sensor_system_id) for entity_id in entity_ids):
                        await sensor.HealthPollerController.start(device_id)

                    for sensor_type in config.SensorTypes.get_all():
                        if sensor_type not in (config.SensorTypes.VIDEO_SIGNAL, config.SensorTypes.SYSTEM_STATUS):
                            sensor_id = config.Devices.get(device_id=device_id, key=f"sensor-{sensor_type}-id")
                            if sensor_id in entity_ids:
                                await sensor.update_setting(device_id, sensor_type)

                    for select_type in config.SelectTypes.get_all():
                        select_id = config.Devices.get(device_id=device_id, key=f"select-{select_type}-id")
                        if select_id in entity_ids:
                            await selects.update_attributes(device_id, select_type)

            except OSError as e:
                _LOG.critical(e)
                _LOG.info("This usually happens when the hostname of the device running the integration has changed which is used to decrypt the password")
                _LOG.info("Please either use the old hostname or configure the device again and enter the passwort to decrypt it using the new hostname")



#BUG #WAIT No event when removing an entity as configured entity. Could be a UC Python library or core/web configurator bug.
# https://github.com/unfoldedcircle/integration-python-library/issues/25
# Therefore poller tasks will also be running for entities that have been removed as configured entities
@api.listens_to(ucapi.Events.UNSUBSCRIBE_ENTITIES)
async def on_unsubscribe_entities(entity_ids: list[str]) -> None:
    """
    Unsubscribe to given entities.

    Just show a debug log message as there is no permanent connection to the projector or clients that needs to be closed or removed.
    """
    _LOG.info("Received unsubscribe entities event for entity ids: " + str(entity_ids))

    config.Setup.set(config.Setup.Keys.STANDBY, False)

    device_ids = []

    for entity_id in entity_ids:
        # First, check if entity_id is directly a device_id (media player entity)
        if entity_id in config.Devices.list():
            device_ids.append(entity_id)
        else:
            # Try to extract device_id from entity_id (for sensor, remote, select entities)
            extracted_device_id = config.Devices.extract_device_id_from_entity_id(entity_id)
            if extracted_device_id and extracted_device_id not in device_ids:
                device_ids.append(extracted_device_id)

    if not device_ids:
        _LOG.info("No valid device ids found in entity ids list from entity subscribe message")

    else:
        for device_id in device_ids:

            for entity_id in entity_ids:
                mp_entity_id= config.Devices.get(device_id=entity_id, key=config.DevicesKeys.DEVICE_ID)
                rt_entity_id = config.Devices.get(device_id=entity_id, key="remote-id")
                device_id = mp_entity_id

                if mp_entity_id in entity_ids:
                    await media_player.MpPollerController.stop(device_id=entity_id)
                    await media_player.remove(device_id=entity_id)

                if rt_entity_id in entity_ids:
                    await remote.remove(device_id=entity_id)

                removed_sensor_ids = []
                for sensor_type in config.SensorTypes.get_all():
                    sensor_id = config.Devices.get(device_id=entity_id, key=f"sensor-{sensor_type}-{device_id}")
                    if sensor_id in entity_ids:
                        removed_sensor_ids.append(sensor_id)
                        await sensor.remove(device_id=entity_id, sensor_type=sensor_type)

                for removed_sensor_id in removed_sensor_ids:
                    if removed_sensor_id in entity_ids:
                        await sensor.HealthPollerController.stop(device_id=entity_id)

                removed_select_ids = []
                for select_type in config.SelectTypes.get_all():
                    select_id = config.Devices.get(device_id=entity_id, key=f"select-{select_type}-{device_id}")
                    if select_id in entity_ids:
                        removed_select_ids.append(select_id)
                        await selects.remove(device_id=entity_id, select_type=select_type)



def setup_logger():
    """Get logger from all modules"""

    level = os.getenv("UC_LOG_LEVEL", "DEBUG").upper()

    logging.getLogger("ucapi.api").setLevel(level)
    logging.getLogger("ucapi.entities").setLevel(level)
    logging.getLogger("ucapi.entity").setLevel(level)
    logging.getLogger("driver").setLevel(level)
    logging.getLogger("projector").setLevel(level)
    logging.getLogger("adcp").setLevel(level)
    logging.getLogger("config").setLevel(level)
    logging.getLogger("setup").setLevel(level)
    logging.getLogger("media_player").setLevel(level)
    logging.getLogger("remote").setLevel(level)
    logging.getLogger("sensor").setLevel(level)
    logging.getLogger("selects").setLevel(level)



class JournaldFormatter(logging.Formatter):
    """Formatter for journald. Prefixes messages with priority level."""

    def format(self, record):
        """Format the log record with journald priority prefix."""
        # mapping of logging levels to journald priority levels
        # https://www.freedesktop.org/software/systemd/man/latest/sd-daemon.html#syslog-compatible-log-levels
        # Note: DEBUG app messages are logged with priority 6 (info) and INFO with priority 5 (notice)
        # This is a workaround until the log subsystem on the Remote is updated to support debug levels.
        priority = {
            logging.DEBUG: "<6>", # SD_INFO
            logging.INFO: "<5>", # SD_NOTICE
            logging.WARNING: "<4>",
            logging.ERROR: "<3>",
            logging.CRITICAL: "<2>",
        }.get(record.levelno, "<6>")
        return f"{priority}{record.name:<14s} | {record.getMessage()}"



async def main():
    """Main function that gets logging from all sub modules and starts the driver"""

    if os.getenv("INVOCATION_ID"):
        # when running under systemd: timestamps are added by the journal
        # and we use a custom formatter for journald priority levels
        handler = logging.StreamHandler()
        handler.setFormatter(JournaldFormatter())
        logging.basicConfig(handlers=[handler])
    else:
        logging.basicConfig(
            format="%(asctime)s.%(msecs)03d | %(levelname)-8s | %(name)-14s | %(message)s",
            datefmt="%Y-%m-%d %H:%M:%S",
        )

    setup_logger()

    #Check if integration runs in a PyInstaller bundle on the remote and adjust the logging format, config file path and disable power/mute/input poller task
    if getattr(sys, "frozen", False) and hasattr(sys, "_MEIPASS"):

        _LOG.info("This integration is running in a PyInstaller bundle. Probably on the remote hardware")
        config.Setup.set(config.Setup.Keys.BUNDLE_MODE, True)

        cfg_path = os.environ["UC_CONFIG_HOME"] + "/config.json"
        config.Setup.set(config.Setup.Keys.CFG_PATH, cfg_path)
        _LOG.info("The configuration is stored in " + cfg_path)

        _LOG.info("Disabling power/mute/input and health poller task to reduce battery consumption when running on the remote")
        _LOG.info("The pollers can still be enabled afterwards if a custom interval has been set in the manual advanced setup")
        config.Setup.set(config.Setup.Keys.DEFAULT_POLLER_INTERVAL_MEDIA_PLAYER, 0, False) #Using False to prevent the config file from being created before first time setup

    _LOG.debug("Starting driver initialization")

    await setup.init()

    try:
        config.Setup.load()
        config.Devices.load()
    except (OSError, Exception) as e:
        _LOG.critical(e)
        _LOG.critical("Stopping integration driver due to a critical error during loading of configuration or device data")
        raise SystemExit(0) from e

    if config.Setup.get(config.Setup.Keys.SETUP_COMPLETE):
        await add_available_entities()


if __name__ == "__main__":
    try:
        loop.run_until_complete(main())
        loop.run_forever()
    except KeyboardInterrupt:
        pass
