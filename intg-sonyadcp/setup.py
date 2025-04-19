#!/usr/bin/env python3

"""Module that includes all functions needed for the setup and reconfiguration process"""

import logging

from ipaddress import ip_address
import socket
import ucapi

import config
import driver
import projector
import media_player
import sensor
import remote
import adcp as ADCP

_LOG = logging.getLogger(__name__)



async def init():
    """Advertises the driver metadata and first setup page to the remote using driver.json"""
    await driver.api.init("driver.json", driver_setup_handler)



async def driver_setup_handler(msg: ucapi.SetupDriver) -> ucapi.SetupAction:
    """
    Dispatch driver setup requests to corresponding handlers.

    Either start the setup process or handle the provided user input data.

    :param msg: the setup driver request object, either DriverSetupRequest,
                UserDataResponse or UserConfirmationResponse
    :return: the setup action on how to continue
    """

    if isinstance(msg, ucapi.DriverSetupRequest):
        if msg.reconfigure:
            config.Setup.set("setup_reconfigure", True)
            return await show_setup_action()
        config.Setup.set("setup_reconfigure", False)
        return await show_setup_basic()
    if isinstance(msg, ucapi.UserDataResponse):
        if config.Setup.get("setup_step") == "basic" or config.Setup.get("setup_step") == "basic_reconfigure":
            return await handle_response_basic(msg)
        if config.Setup.get("setup_step") == "advanced" or config.Setup.get("setup_step") == "advanced_reconfigure":
            return await handle_response_advanced(msg)
        if config.Setup.get("setup_step") == "action":
            return await handle_response_action(msg)
        if config.Setup.get("setup_step") == "choose_device":
            return await handle_response_choose_device(msg)
    elif isinstance(msg, ucapi.AbortDriverSetup):
        _LOG.info("Setup was aborted with code: %s", msg.error)

    _LOG.error("Error during setup")
    config.Setup.set("setup_complete", False)

    if config.Setup.get("setup_temp_device") != "":
        _LOG.info("Removing the setup temp device from config and stopping poller tasks for this device")
        await media_player.MpPollerController.stop(config.Setup.get("setup_temp_device"))
        await sensor.LtPollerController.stop(config.Setup.get("setup_temp_device"))
        try:
            config.Devices.remove(config.Setup.get("setup_temp_device"))
        except ValueError:
            pass

    config.Setup.set("setup_step", "init")
    config.Setup.set("setup_auto_discovery", False)

    if config.Setup.get("setup_reconfigure") is True:
        _LOG.info("Resetting reconfigure setup device id")
        config.Setup.set("setup_reconfigure_device", "")

    return ucapi.SetupError()



async def show_setup_action() -> ucapi.SetupAction:
    """
    Start driver reconfiguration setup.

    :param msg: value(s) of input fields in the first setup screen.
    :return: the setup action on how to continue
    """

    _LOG.info("Showing reconfiguration options")

    configured_devices = []
    actions = [
                {"id": "reconfigure", "label": {"en": "Re-configure selected device", "de": "Ausgewähltes Gerät bearbeiten"}},
                {"id": "add", "label": {"en": "Add new device", "de": "Neues Gerät hinzufügen"}}
                ]

    try:
        for device_id in config.Devices.list():
            name = config.Devices.get(device_id, "name")
            configured_devices.append({"id": device_id, "label": {"en": name}})
    except Exception:
        return ucapi.SetupError()

    config.Setup.set("setup_step", "action")

    return ucapi.RequestUserInput(
        {
            "en": "Reconfigure Actions",
            "de": "Aktionen für die Neu-Konfigurierung"
        },
        [
            {
                "id": "notes",
                "label": {"en": "Re-configure setup", "de": "Konfiguration"},
                "field": { "label": {
                        "value": {
                                "en": "Here you can change settings of configured devices or add a new device",
                                "de": "Hier kannst du Einstellungen von konfigurierten Geräten erneut anpassen oder neue Geräte hinzufügen"
                            } }
                            }
            },
            {
                "id": "device",
                "label": {
                    "en": "Configured devices:",
                    "de": "Konfigurierte Geräte:"
                    },
                "field": {"dropdown": {
                                    "value": configured_devices[0]["id"],
                                    "items": configured_devices
                                    }
                        },
            },
            {
                "id": "action",
                "label": {
                    "en": "Action:",
                    "de": "Aktion:"
                    },
                "field": {"dropdown": {
                                    "value": actions[0]["id"],
                                    "items": actions
                                    }
                        },
            },
        ]
    )



async def handle_response_action(msg: ucapi.DriverSetupRequest,) -> ucapi.SetupAction:
    """
    Handle the reconfigure action from the user response

    :param msg: value(s) of input fields in the first setup screen.
    :return: the setup action on how to continue
    """

    action = msg.input_values["action"]
    device_id = msg.input_values["device"]

    if action == "add":
        _LOG.info("Configure a new device")
        return await show_setup_basic()

    if action == "reconfigure":
        _LOG.info(f"Re-configure device \"{device_id}\"")
        config.Setup.set("setup_reconfigure_device", device_id)
        return await show_setup_basic(device_id)



async def show_setup_basic(device_id = None) -> ucapi.SetupAction:
    """
    Add a new or configure an existing device and show basic configuration

    :param msg: value(s) of input fields in the first setup screen.
    :return: the setup action on how to continue
    """

    if device_id is None:
        _LOG.info("Starting basic setup for a new device")
        ip = ""
        adcp_password = ""

        config.Setup.set("setup_step", "basic")
    else:
        _LOG.info(F"Starting basic reconfigure setup for device \"{device_id}\"")
        ip = config.Devices.get(device_id, "ip")
        adcp_password = config.Setup.get("setup_masked_password")

        config.Setup.set("setup_step", "basic_reconfigure")

    #TODO Find out why Masked: True gets ignored and doesn't mask passwords in ucapi debug log messages like in:
    # https://github.com/FYTA-GmbH/uc-integration-fyta/blob/31e27e660d56243c4fe6158220f036a2cdb3f340/driver.py#L199
    return ucapi.RequestUserInput(
            {
                "en": "Basic Setup",
                "de": "Allgemeine Einrichtung"
            },
            [
                {
                    "id": "notes",
                    "label": {"en": "Basic Setup", "de": "Allgemeine Einrichtung"},
                    "field": { "label": {
                        "value": {
                                "en": "If you leave the ip field empty an attempt is made to **automatically find projectors** \
    via the SDAP advertisement service in your local network. \n\nData is only send **every 30 seconds by default**. \
    The search runs for 31 seconds to find all devices in your network.",
                                "de": "Wenn du das Feld für die IP-Adresse leer lässt, wird versucht den Projektor per SDAP **automatisch \
    in deinem lokalen Netzwerk zu finden**\n\nDie Daten werden **standardmäßig nur alle 30 Sekunden** vom Projektor gesendet. \
    Die Suche läuft 31 Sekunden, um alle Geräte im Netzwerk zu finden."
                            } }
                            }
                },
                {
                    "id": "ip",
                    "label": {
                            "en": "Projector IP (leave empty to use auto discovery):",
                            "de": "Projektor-IP (leer lassen zur automatischen Erkennung):"
                            },
                    "field": {"text": {
                                    "value": ip
                                    }
                            }
                },
                {
                    "id": "adcp_password",
                    "label": {
                            "en": "ADCP / WebUI password (only required if ADCP authentication is turned on):",
                            "de": "ADCP / WebUI-Passwort (nur erforderlich bei aktivierter ADCP-Authentifizierung):"
                            },
                    "field": {
                        "text": {
                            "value": adcp_password,
                            "masked": True
                        }
                    },
                },
                {
                    "id": "notes",
                    "label": {"en": "Advanced settings", "de": "Erweiterte Einstellungen"},
                    "field": { "label": {
                        "value": {
                                    "en": "If you have changed the default ADCP or SDAP ports, change timeouts \
    or the poller intervals you need to configure them in the advanced settings",
                                    "de":"Wenn du die ADCP oder SDAP Standard-Ports geändert hast, Timeouts oder \
    Poller-Intervalle ändern möchtest, musst du diese in den erweiterten Einstellungen konfigurieren"
                                } }
                            }
                },
                {
                    "id": "advanced_settings",
                    "label": {"en": "Configure advanced settings", "de": "Erweiterte Einstellungen konfigurieren"},
                    "field": {
                    "checkbox": {
                        "value": False
                        }
                    }
                }
            ]
        )


async def handle_response_basic(msg: ucapi.UserDataResponse) -> ucapi.SetupAction:
    """
    Process user data response in a setup process.

    Driver setup callback to provide requested user data during the setup process.

    :param msg: response data from the requested user data
    :return: the setup action on how to continue: SetupComplete if finished.
    """

    ip = msg.input_values["ip"]
    adcp_password = msg.input_values["adcp_password"]
    advanced_settings = msg.input_values["advanced_settings"]

    if ip != "":
        #Check if input is a valid ipv4 or ipv6 address
        _LOG.info("Entered ip address: " + ip)
        try:
            ip_address(ip)
        except ValueError:
            _LOG.error("The entered ip address \"" + ip + "\" is not valid")
            return ucapi.SetupError(error_type=ucapi.IntegrationSetupError.NOT_FOUND)
    else:
        _LOG.info("No ip address entered. Using auto discovery mode")
        config.Setup.set("setup_auto_discovery", True)

    if ip != "" and config.Setup.get("setup_step") == "basic":
        config.Devices.add(entity_data={"ip": ip})

    if config.Setup.get("setup_step") == "basic_reconfigure":
        device_id = config.Setup.get("setup_reconfigure_device")
        current_ip = config.Devices.get(device_id, "ip")
        if ip == current_ip :
            _LOG.debug("IP has not been changed")
        else:
            config.Devices.add(device_id=device_id, entity_data={"ip": ip})

    if adcp_password == "":
        _LOG.info("No ADCP password entered. Assuming ADCP authentication is not enabled")
    else:
        if config.Setup.get("setup_step") == "basic_reconfigure":
            device_id = config.Setup.get("setup_reconfigure_device")
            if adcp_password != config.Setup.get("setup_masked_password"):
                config.Devices.add(device_id=device_id, entity_data={"adcp_password": adcp_password})
            else:
                _LOG.debug("ADCP password has not been changed")
        else:
            config.Devices.add(entity_data={"adcp_password": adcp_password})

    if advanced_settings == "false":
        if config.Setup.get("setup_auto_discovery") is False:
            return await validate_entity_data()
        return await query_projector_data()

    if advanced_settings == "true":
        return await show_setup_advanced()



async def show_setup_advanced():
    """Show the advanced setup settings"""

    _LOG.info("Show advanced setup settings")

    try:
        if config.Setup.get("setup_step") == "basic_reconfigure":
            device_id = config.Setup.get("setup_reconfigure_device")
            adcp_port = config.Devices.get(device_id, "adcp_port")
            adcp_timeout = config.Devices.get(device_id, "adcp_timeout")
            sdap_port = config.Devices.get(device_id, "sdap_port")
            mp_poller_interval = config.Devices.get(device_id, "mp_poller_interval")
            lt_poller_interval = config.Devices.get(device_id, "lt_poller_interval")
            config.Setup.set("setup_step", "advanced_reconfigure")
        else:
            adcp_port = config.Setup.get("default_adcp_port")
            adcp_timeout = config.Setup.get("default_adcp_timeout")
            sdap_port = config.Setup.get("default_sdap_port")
            mp_poller_interval = config.Setup.get("default_mp_poller_interval")
            lt_poller_interval = config.Setup.get("default_lt_poller_interval")
            config.Setup.set("setup_step", "advanced")
    except ValueError as v:
        _LOG.error(v)

    adcp_port = adcp_port if adcp_port is not None else config.Setup.get("default_adcp_port")
    adcp_timeout = adcp_timeout if adcp_timeout is not None else config.Setup.get("default_adcp_timeout")
    sdap_port = sdap_port if sdap_port is not None else config.Setup.get("default_sdap_port")
    mp_poller_interval = mp_poller_interval if mp_poller_interval is not None else config.Setup.get("default_mp_poller_interval")
    lt_poller_interval = lt_poller_interval if lt_poller_interval is not None else config.Setup.get("default_lt_poller_interval")

    return ucapi.RequestUserInput(
        {
            "en": "Advanced Settings",
            "de": "Erweiterte Einstellungen"
        },
        [
            {
                "id": "adcp_port",
                "label": {
                        "en": "ADCP control port (TCP):",
                        "de": "ADCP Steuerungs-Port (TCP):"
                        },
                "field": {"number": {
                                "value": adcp_port,
                                "decimals": 1
                                    }
                        }
            },
            {
                "id": "adcp_timeout",
                "label": {
                        "en": "ADCP timeout:",
                        "de": "ADCP-Timeout:"
                        },
                "field": {"number": {
                                "value": adcp_timeout,
                                "decimals": 1
                                    }
                        }
            },
            {
                "id": "sdap_port",
                "label": {
                        "en": "SDAP advertisement port (UDP):",
                        "de": "SDAP Ankündigungs-Port (UDP):"
                        },
                "field": {"number": {
                                "value": sdap_port,
                                "decimals": 1
                                    }
                        }
            },
            {
                "id": "note",
                "label": {"en": "Poller intervals", "de": "Poller-Intervalle"},
                "field": { "label": { "value": {
                    "en":
                        "When running this integration as a custom integration on the remote itself it is best not to change these intervals or \
                        set them as high as possible to reduce battery consumption and save cpu/memory usage. \
                        An interval set to high can lead to unstable system performance.",
                    "de":
                        "Wenn du diese Integration als Custom Integration auf der Remote selbst laufen lässt, ändere diese Intervalle am Besten nicht oder \
                        setze sie möglichst hoch, um den Batterieverbrauch zu reduzieren und die CPU-/Arbeitsspeichernutzung zu verringern. \
                        Ein zu hoher Intervall kann zu einem instabilen System führen."
                    } }
                }
            },
            {
                "id": "mp_poller_interval",
                "label": {
                        "en": "Projector power/mute/input poller interval (in seconds, 0 to deactivate):",
                        "de": "Projektor Power/Mute/Eingang Poller-Interval (in Sekunden, 0 zum Deaktivieren):"
                        },
                "field": {"number": {
                                "value": mp_poller_interval,
                                "decimals": 1
                                    }
                        }
            },
            {
                "id": "lt_poller_interval",
                "label": {
                        "en": "Light source timer poller interval (in seconds, 0 to deactivate):",
                        "de": "Lichtquellen-Poller-Interval (in Sekunden, 0 zum Deaktivieren):"
                        },
                "field": {"number": {
                                "value": lt_poller_interval,
                                "decimals": 1
                                    }
                        }
            }
        ]
    )



async def handle_response_advanced(msg: ucapi.UserDataResponse) -> ucapi.SetupAction:
    """ Process user data response in a setup process for advanced settings"""

    try:
        device_id = config.Setup.get("setup_reconfigure_device")
    except ValueError:
        device_id = None

    ip = msg.input_values["ip"]
    adcp_port = int(msg.input_values["adcp_port"])
    adcp_timeout = int(msg.input_values["adcp_timeout"])
    sdap_port = int(msg.input_values["sdap_port"])
    mp_poller_interval = int(msg.input_values["mp_poller_interval"])
    lt_poller_interval = int(msg.input_values["lt_poller_interval"])

    skip_entities = False

    if config.Setup.get("setup_step") == "advanced_reconfigure":
        if config.Devices.get(device_id, "adcp_port") is None and config.Devices.get(device_id, "sdap_port") is None:
            skip_entities = True
        else:
            if ip == config.Devices.get(device_id, "ip") and adcp_port == config.Devices.get(device_id, "adcp_port") \
            and sdap_port == config.Devices.get(device_id, "sdap_port"):
                _LOG.info("No entity validation related values have been changed. Skipping entity validation and creation")
                skip_entities = True

    try:
        if skip_entities is False:

            if adcp_port != config.Setup.get("default_adcp_port"):
                config.Devices.add(device_id=device_id, entity_data={"adcp_port": adcp_port})
            else:
                #Remove existing value if it is changed back to the default value
                if config.Devices.get(device_id=device_id, key="adcp_port") is not None:
                    _LOG.debug("ADCP port has been changed back to default value. Removing from config")
                    config.Devices.remove(device_id=device_id, key="adcp_port")

            if sdap_port != config.Setup.get("default_sdap_port"):
                config.Devices.add(device_id=device_id, entity_data={"sdap_port": sdap_port})
            else:
                if config.Devices.get(device_id=device_id, key="sdap_port") is not None:
                    _LOG.debug("SDAP port has been changed back to default value. Removing from config")
                    config.Devices.remove(device_id=device_id, key="sdap_port")

        if adcp_timeout != config.Setup.get("default_adcp_timeout"):
            config.Devices.add(device_id=device_id, entity_data={"adcp_timeout": adcp_timeout})
        else:
            if config.Devices.get(device_id=device_id, key="adcp_timeout") is not None:
                _LOG.debug("ADCP timeout has been changed back to default value. Removing from config")
                config.Devices.remove(device_id=device_id, key="adcp_timeout")

        if mp_poller_interval != config.Setup.get("default_mp_poller_interval"):
            config.Devices.add(device_id=device_id, entity_data={"mp_poller_interval": mp_poller_interval})
        else:
            if config.Devices.get(device_id=device_id, key="mp_poller_interval") is not None:
                _LOG.debug("Mp poller interval has been changed back to default value. Removing from config")
                config.Devices.remove(device_id=device_id, key="mp_poller_interval")

        if lt_poller_interval != config.Setup.get("default_lt_poller_interval"):
            config.Devices.add(device_id=device_id, entity_data={"lt_poller_interval": lt_poller_interval})
        else:
            if config.Devices.get(device_id=device_id, key="lt_poller_interval") is not None:
                _LOG.debug("Lt poller interval has been changed back to default value. Removing from config")
                config.Devices.remove(device_id=device_id, key="lt_poller_interval")

    except ValueError as v:
        _LOG.error(v)
        return ucapi.SetupError()

    if not skip_entities:
        try:
            return await query_projector_data()
        except ConnectionRefusedError:
            _LOG.error("Connection to projector refused. Please check that the device is reachable from the same network \
as the remote and advertisement and ADCP are activated in the projectors web interface")
            return ucapi.SetupError(error_type=ucapi.IntegrationSetupError.CONNECTION_REFUSED)
        except TimeoutError as t:
            _LOG.error(t)
            return ucapi.SetupError(error_type=ucapi.IntegrationSetupError.TIMEOUT)
        except ValueError as v:
            _LOG.error(v)
            return ucapi.SetupError(error_type=ucapi.IntegrationSetupError.NOT_FOUND)
        except PermissionError as p:
            _LOG.error(p)
            return ucapi.SetupError(error_type=ucapi.IntegrationSetupError.AUTHORIZATION_ERROR)
        except Exception as e:
            _LOG.error(f"An error occurred while retrieving projector data: {e}")
            return ucapi.SetupError()
    else:
        return await complete_setup(device_id=device_id, skip_entities=True)



async def query_projector_data():
    """Retrieves the ip and data from the projector (serial number & model name).
    Either via the SDAP protocol which can take up to 30 seconds when the default advertisement interval has not been changed
    or via ADCP commands if the ip has been manually entered in the setup
    
    Afterwards this data will be used to generate the entity id and name and sets and stores them to the runtime storage and config file

    :ip: If empty the ip retrieved via SDAP will be used
    """

    if not config.Setup.get("setup_auto_discovery"):
        return await validate_entity_data()

    _LOG.info("Query ip, model name and serial number from projector via SDAP advertisement service")
    _LOG.info("The search will run for 30 seconds and list all devices that have been discovered")

    try:
        devices = await projector.projector_def().get_pjinfo()
    except Exception as e:
        raise Exception(e) from e

    if devices is not None:
        _LOG.info("Got data from projector")

        if devices and len(devices) > 1:
            _LOG.info("More than one projector have been discovered")
            config.Setup.set("setup_step", "choose_device")

            devices_dropdown = []
            for device in devices:
                name = device["model"]
                ip = device["ip"]
                devices_dropdown.append({"id": ip, "label": {"en": f"{name} ({ip})"}})
                #TODO Add a check if the ip is already in the config file and remove it from devices_dropdown

            return ucapi.RequestUserInput(
            {
                "en": "Auto discovery selection",
                "de": "Auswahl für Auto-Entdeckung"
            },
            [
                {
                    "id": "notes",
                    "label": {"en": "Multiple devices discovered", "de": "Mehrere Geräte entdeckt"},
                    "field": { "label": {
                            "value": {
                                    "en": "Please choose a device",
                                    "de": "Bitte wähle ein Gerät aus"
                                } }
                                }
                },
                {
                    "id": "device",
                    "label": {
                        "en": "Discovered devices:",
                        "de": "Entdeckte Geräte:"
                        },
                    "field": {"dropdown": {
                                        "value": devices_dropdown[0]["id"],
                                        "items": devices_dropdown
                                        }
                            },
                },
            ]
            )

        device = devices[0]

        if device["ip"] != "":
            ip = device["ip"]
            _LOG.info("Automatic discovered IP: " + ip)
            config.Devices.add(entity_data={"ip": ip})
        else:
            raise ValueError("Got empty ip from projector")

        if device["model"] or str(device["serial"]) != "":
            model = device["model"]
            serial = str(device["serial"])
        else:
            raise Exception("Got empty model and serial from projector")

        return await validate_entity_data(model, serial)

    raise TimeoutError("Received no projector data within the given timeout. Please check if advertisement is activated \
in the projectors web interface and the interval is <= 30 seconds. Also check that the integration is running in the same (sub) network as the projector")



async def handle_response_choose_device(msg: ucapi.UserDataResponse) -> ucapi.SetupAction:
    """Handles the device selection response from the user"""

    ip = msg.input_values["device"]

    try:
        config.Devices.add(entity_data={"ip": ip})
    except Exception as e:
        raise Exception(e) from e

    return await validate_entity_data()



async def validate_entity_data(model:str = None, serial:str = None):
    """Checks ADCP port and password and generate final device_id and name"""

    skip_entities = False

    try:
        config.Setup.get("setup_reconfigure_device")
    except ValueError:
        device_id = None
        adcp_port = config.Devices.get(key="adcp_port")
        ip = config.Devices.get(key="ip")
    else:
        skip_entities = True
        device_id = config.Setup.get("setup_reconfigure_device")
        adcp_port = config.Devices.get(device_id, "adcp_port")
        ip = config.Devices.get(device_id, "ip")

    adcp_port = adcp_port if adcp_port is not None else config.Setup.get("default_adcp_port")

    #Check if adcp port is open
    if not port_check(ip, adcp_port):
        _LOG.error("Timeout while connecting to ADCP port " + str(adcp_port) + " on " + ip)
        _LOG.info("Please check if you entered the correct ip of the projector and ADCP is activated and running on port " + str(adcp_port))
        raise ConnectionRefusedError

    #Check if ADCP password is correct with a test command
    _LOG.info("Sending ADCP test command")
    try:
        await projector.get_light_source_hours(device_id)
    except Exception as e:
        error = str(e)
        if error:
            _LOG.error(error)
        _LOG.error("Test command failed")
        raise type(e)(error) from e

    if not skip_entities:
        if model is None and serial is None:
            _LOG.info("Retrieving model name and serial number via ADCP commands")
            try:
                model_raw = await projector.projector_def(device_id).command(ADCP.Get.MODEL)
                serial_raw = await projector.projector_def(device_id).command(ADCP.Get.SERIAL)
            except Exception as e:
                raise type(e)(str(e)) from e

            model = model_raw.strip("\"")
            serial = serial_raw.strip("\"")

        device_id = model + "-" + serial
        device_name= "Sony " + model

        _LOG.debug("Generated device id and name from serial number and model name")
        _LOG.debug("Device ID: " + device_id)
        _LOG.debug("Device Name: " + device_name)

        config.Devices.add(new_device_id=device_id, entity_data={"name": device_name})

        return await complete_setup(device_id=device_id, skip_entities=skip_entities)

    return await complete_setup(device_id=device_id, skip_entities=skip_entities)



def port_check(ip, port):
    """Function to check if a specified port from a specified ip is open"""

    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    s.settimeout(2)
    try:
        s.connect((ip, int(port)))
        s.shutdown(socket.SHUT_RDWR)
        return True
    except Exception:
        return False
    finally:
        s.close()



async def complete_setup(device_id:str = None, skip_entities:bool = False) -> ucapi.SetupAction:
    """Complete the setup process by creating the entities and starting the poller tasks"""

    if not skip_entities and device_id is not None:
        try:
            config.Devices.set_remote_and_sensor_data(device_id=device_id)
        except ValueError as v:
            _LOG.error(v)
            return ucapi.SetupError()

        await media_player.add_mp(device_id)
        await remote.add_remote(device_id)
        await sensor.add_lt_sensor(device_id)

    if config.Setup.get("setup_reconfigure") is True:
        #During the initial setup all needed pollers tasks will be started with the subscribe entities event
        await media_player.MpPollerController.start(device_id)
        await sensor.LtPollerController.start(device_id)

    config.Setup.set("setup_complete", True)
    _LOG.info("Setup complete")

    return ucapi.SetupComplete()
