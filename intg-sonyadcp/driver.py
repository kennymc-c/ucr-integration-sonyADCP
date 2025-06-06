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
import sensor
import remote

_LOG = logging.getLogger("driver")  # avoid having __main__ in log messages

loop = asyncio.get_event_loop()
api = ucapi.IntegrationAPI(loop)



async def startcheck():
    """
    Called at the start of the integration driver to load the config file into the runtime storage and add all needed entities and create attributes poller tasks
    """
    try:
        config.Setup.load()
        config.Devices.load()
    except (OSError, Exception) as e:
        _LOG.critical(e)
        _LOG.critical("Stopping integration driver")
        raise SystemExit(0) from e

    if config.Setup.get("setup_complete"):
        for device_id in config.Devices.list():
            try:
                mp_entity_id = device_id
                rt_entity_id = mp_entity_id
                lt_entity_id = config.Devices.get(device_id=device_id, key="lt-id")
            except ValueError as v:
                _LOG.error(v)

            #Add all entities as available entities
            if api.available_entities.contains(mp_entity_id):
                _LOG.debug("Projector media player entity with id " + mp_entity_id + " is already in storage as available entity")
            else:
                await media_player.add_mp(device_id)

            if api.available_entities.contains(rt_entity_id):
                _LOG.debug("Projector remote entity with id " + rt_entity_id + " is already in storage as available entity")
            else:
                await remote.add_remote(device_id)

            if api.available_entities.contains(lt_entity_id):
                _LOG.debug("Projector light source timer sensor entity with id " + lt_entity_id + " is already in storage as available entity")
            else:
                await sensor.add_lt_sensor(device_id)
    else:
        if len(config.Devices.list()) < 1:
            _LOG.info("First time setup was not completed. Please restart the setup process")
        else:
            _LOG.info("Please start the driver setup process")



@api.listens_to(ucapi.Events.CONNECT)
async def on_r2_connect() -> None:
    """
    Connect notification from Remote Two.

    Just reply with connected as there is no permanent connection to the projector that needs to be re-established
    """
    _LOG.info("Received connect event message from remote")

    await api.set_device_state(ucapi.DeviceStates.CONNECTED)



@api.listens_to(ucapi.Events.DISCONNECT)
async def on_r2_disconnect() -> None:
    """
    Disconnect notification from the remote Two.

    Just reply with disconnected as there is no permanent connection to the projector that needs to be closed
    """
    _LOG.info("Received disconnect event message from remote")

    await api.set_device_state(ucapi.DeviceStates.DISCONNECTED)



@api.listens_to(ucapi.Events.ENTER_STANDBY)
async def on_r2_enter_standby() -> None:
    """
    Enter standby notification from Remote Two.

    Set config.R2_IN_STANDBY to True and show a debug log message as there is no permanent connection to the projector that needs to be closed.
    """
    _LOG.info("Received enter standby event message from remote")

    _LOG.debug("Set config.R2_IN_STANDBY to True")
    config.Setup.set("standby", True)



@api.listens_to(ucapi.Events.EXIT_STANDBY)
async def on_r2_exit_standby() -> None:
    """
    Exit standby notification from Remote Two.

    Just show a debug log message as there is no permanent connection to the projector that needs to be re-established.
    """
    _LOG.info("Received exit standby event message from remote")

    _LOG.debug("Set config.R2_IN_STANDBY to False")
    config.Setup.set("standby", False)



@api.listens_to(ucapi.Events.SUBSCRIBE_ENTITIES)
async def on_subscribe_entities(entity_ids: list[str]) -> None:
    """
    Subscribe to given entities.

    :param entity_ids: entity identifiers.
    """
    _LOG.info("Received subscribe entities event for entity ids: " + str(entity_ids))

    config.Setup.set("standby", False)

    if config.Setup.get("setup_complete"):
        for entity_id in entity_ids:
            device_id = None
            mp_entity_id = None
            rt_entity_id = None
            lt_entity_id = None

            if entity_id in config.Devices.list():
                device_id = config.Devices.get(device_id=entity_id, key="device_id")
                mp_entity_id = device_id
                rt_entity_id = config.Devices.get(device_id=entity_id, key="rt-id")
                lt_entity_id = config.Devices.get(device_id=device_id, key="lt-id")

            try:
                if mp_entity_id and entity_id == mp_entity_id:
                    await media_player.update_mp(device_id)
                    await media_player.MpPollerController.start(device_id)
                if lt_entity_id and entity_id == lt_entity_id:
                    await sensor.update_lt(device_id)
                    await sensor.LtPollerController.start(device_id)
                if rt_entity_id and entity_id == rt_entity_id:
                    await remote.update_rt(device_id)
            except OSError as o:
                _LOG.critical(o)
            except Exception as e:
                error_msg = str(e)
                if error_msg:
                    _LOG.warning(f"Failed to update attributes for entity {entity_id}")
                    _LOG.warning(error_msg)
                else:
                    _LOG.warning(f"Failed to update attributes for entity {entity_id}")



#BUG No event when removing an entity as configured entity. Could be a UC Python library or core/web configurator bug.
# https://github.com/unfoldedcircle/integration-python-library/issues/25
# Therefore poller tasks will also be running for entities that have been removed as configured entities
@api.listens_to(ucapi.Events.UNSUBSCRIBE_ENTITIES)
async def on_unsubscribe_entities(entity_ids: list[str]) -> None:
    """
    Unsubscribe to given entities.

    Just show a debug log message as there is no permanent connection to the projector or clients that needs to be closed or removed.
    """
    _LOG.info("Received unsubscribe entities event for entity ids: " + str(entity_ids))

    config.Setup.set("standby", False)

    for entity_id in entity_ids:
        mp_entity_id= config.Devices.get(device_id=entity_id, key="id")
        lt_entity_id = config.Devices.get(device_id=entity_id, key="lt-id")

        if mp_entity_id in entity_ids:
            await media_player.MpPollerController.stop(device_id=entity_id)

        if lt_entity_id in entity_ids:
            await sensor.LtPollerController.stop(device_id=entity_id)



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



async def main():
    """Main function that gets logging from all sub modules and starts the driver"""

    #Check if integration runs in a PyInstaller bundle on the remote and adjust the logging format, config file path and disable power/mute/input poller task
    if getattr(sys, "frozen", False) and hasattr(sys, "_MEIPASS"):

        logging.basicConfig(format="%(name)-14s %(levelname)-8s %(message)s")
        setup_logger()

        _LOG.info("This integration is running in a PyInstaller bundle. Probably on the remote hardware")
        config.Setup.set("bundle_mode", True)

        cfg_path = os.environ["UC_CONFIG_HOME"] + "/config.json"
        config.Setup.set("cfg_path", cfg_path)
        _LOG.info("The configuration is stored in " + cfg_path)

        _LOG.info("Deactivating power/mute/input poller to reduce battery consumption when running on the remote")
        _LOG.info("The poller task may still be activated afterwards if a custom interval has been set in the manual advanced setup")
        config.Setup.set("default_mp_poller_interval", 0, False) #Using False to prevent the config file from being created before first time setup
    else:
        logging.basicConfig(format="%(asctime)s.%(msecs)03d | %(levelname)-8s | %(name)-14s | %(message)s", datefmt="%Y-%m-%d %H:%M:%S")
        setup_logger()

    _LOG.debug("Starting driver")

    await setup.init()
    await startcheck()



if __name__ == "__main__":
    try:
        loop.run_until_complete(main())
        loop.run_forever()
    except KeyboardInterrupt:
        pass
