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
        return await handle_driver_setup(msg)
    if isinstance(msg, ucapi.UserDataResponse):
        if msg.input_values["advanced_settings"] == "true" and config.Setup.get("setup_step") == "basic":
            return await show_advanced_user_data(msg)
        if config.Setup.get("setup_step") == "advanced":
            return await handle_advanced_user_data_response(msg)
        return await handle_basic_user_data_response(msg)
    elif isinstance(msg, ucapi.AbortDriverSetup):
        _LOG.info("Setup was aborted with code: %s", msg.error)

    _LOG.error("Error during setup")
    config.Setup.set("setup_complete", False)

    _LOG.info("Stopping potential already running poller tasks")
    await media_player.MpPollerController.stop()
    await sensor.LtPollerController.stop()

    return ucapi.SetupError()



async def handle_driver_setup(msg: ucapi.DriverSetupRequest,) -> ucapi.SetupAction:
    """
    Start driver setup.

    Initiated by Remote Two to set up the driver.

    :param msg: value(s) of input fields in the first setup screen.
    :return: the setup action on how to continue
    """

    if msg.reconfigure and config.Setup.get("setup_complete"):
        config.Setup.set("setup_reconfigure", True)
        _LOG.info("Starting reconfiguration")
    else:
        _LOG.info("Starting basic setup")

    if not config.Setup.get("setup_complete") and config.Setup.get("setup_reconfigure") is True:
        _LOG.info("Resetting some values for restarting a non complete setup")
        if config.Setup.get("ip") != "":
            _LOG.info("Use empty ip value")
            config.Setup.set("ip", "")
        if config.Setup.get("adcp_password") != "":
            _LOG.info("Clear ADCP password")
            config.Setup.set("adcp_password", "")
        if config.Setup.get("adcp_port") != 53595:
            _LOG.info("Reset ADCP port to the default of 53595")
            config.Setup.set("adcp_port", 53484)
        if config.Setup.get("adcp_timeout") != 5:
            _LOG.info("Reset ADCP timeout to the default of 5 seconds")
            config.Setup.set("adcp_timeout", 5)
        if config.Setup.get("sdap_port") != 53862:
            _LOG.info("Reset SDAP port to the default of 53862")
            config.Setup.set("sdap_port", 53862)

    # IP can be empty during first time setup
    try:
        ip = config.Setup.get("ip")
    except ValueError:
        ip = ""

    adcp_password = config.Setup.get("adcp_password")

    config.Setup.set("setup_step", "basic")

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
                            "en": "If you leave the ip field empty an attempt is made to **automatically find the projector** \
via SDAP advertisement service in your local network. \n\nAll data is only send **every 30 seconds by default**. \
The interval can be shortened to a **minimum of 10 seconds** in the web interface of the projector.",
                            "de": "Wenn du das Feld für die IP-Adresse leer lässt, wird versucht den Projektor per SDAP **automatisch \
in deinem lokalen Netzwerk zu finden**\n\nAlle Daten werden **standardmäßig nur alle 30 Sekunden** vom Projektor gesendet. \
Der Interval kann im Webinterface des Projektors auf **minimal 10 Sekunden** verkürzt werden."
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
                "field": {"text": {
                                "value": adcp_password
                                    }
                        }
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



async def handle_basic_user_data_response(msg: ucapi.UserDataResponse) -> ucapi.SetupAction:
    """
    Process user data response in a setup process.

    Driver setup callback to provide requested user data during the setup process.

    :param msg: response data from the requested user data
    :return: the setup action on how to continue: SetupComplete if finished.
    """

    ip = msg.input_values["ip"]
    adcp_password = msg.input_values["adcp_password"]

    if ip != "":
        #Check if input is a valid ipv4 or ipv6 address
        try:
            ip_address(ip)
        except ValueError:
            _LOG.error("The entered ip address \"" + ip + "\" is not valid")
            return ucapi.SetupError(error_type=ucapi.IntegrationSetupError.NOT_FOUND)
        _LOG.info("Entered ip address: " + ip)
        config.Setup.set("ip", ip)
    else:
        _LOG.info("No ip address entered. Using auto discovery mode")

    skip_entities = False

    if config.Setup.get("setup_reconfigure") is True:
        try:
            ip_old = config.Setup.get("ip")
        except ValueError:
            ip_old = ""
        if adcp_password == config.Setup.get("adcp_password") and ip == ip_old:
            _LOG.info("IP and ADCP password have not been changed. Skipping entity setup and creation.")
            skip_entities = True

    if adcp_password == "":
        _LOG.info("No ADCP password entered. Assuming ADCP authentication is not enabled")
    else:
        config.Setup.set("adcp_password", adcp_password)

    return await complete_setup(skip_entities=skip_entities)



async def show_advanced_user_data(msg: ucapi.UserDataResponse) -> ucapi.SetupAction:
    """Process user data response in a setup process for advanced settings"""

    ip = msg.input_values["ip"]
    adcp_password = msg.input_values["adcp_password"]

    if ip != "":
        #Check if input is a valid ipv4 or ipv6 address
        try:
            ip_address(ip)
        except ValueError:
            _LOG.error("The entered ip address \"" + ip + "\" is not valid")
            return ucapi.SetupError(error_type=ucapi.IntegrationSetupError.NOT_FOUND)
        _LOG.info("Entered ip address: " + ip)
        config.Setup.set("ip", ip)
    else:
        _LOG.info("No ip address entered. Using auto discovery mode")

    if adcp_password == "":
        _LOG.info("No ADCP password entered. Assuming ADCP authentication is not enabled")
    else:
        config.Setup.set("adcp_password", adcp_password)
        

    _LOG.info("Entering Advanced settings")
    config.Setup.set("setup_step", "advanced")

    try:
        adcp_port = config.Setup.get("adcp_port")
        adcp_timeout = config.Setup.get("adcp_timeout")
        sdap_port = config.Setup.get("sdap_port")
        mp_poller_interval = config.Setup.get("mp_poller_interval")
        lt_poller_interval = config.Setup.get("lt_poller_interval")
    except ValueError as v:
        _LOG.error(v)

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



async def handle_advanced_user_data_response(msg: ucapi.UserDataResponse) -> ucapi.SetupAction:
    """ Process user data response in a setup process for advanced settings"""

    adcp_password = config.Setup.get("adcp_password")

    adcp_port = int(msg.input_values["adcp_port"])
    adcp_timeout = int(msg.input_values["adcp_timeout"])
    sdap_port = int(msg.input_values["sdap_port"])
    mp_poller_interval = int(msg.input_values["mp_poller_interval"])
    lt_poller_interval = int(msg.input_values["lt_poller_interval"])

    skip_entities = False
    skip_mp_poller = False
    skip_lt_poller = False

    if config.Setup.get("setup_reconfigure") is True:
        if adcp_password == config.Setup.get("adcp_password") and adcp_port == config.Setup.get("adcp_port") \
        and adcp_timeout == config.Setup.get("adcp_timeout") and sdap_port == config.Setup.get("sdap_port") :
            _LOG.info("No ADCP and SDAP related values have been changed. Skipping entity setup and creation.")
            skip_entities = True

    if mp_poller_interval == config.Setup.get("mp_poller_interval"):
        skip_mp_poller = True
        _LOG.info("Power/mute/input poller interval has not been changed. Skip starting power/mute/input poller task.")
    if lt_poller_interval == config.Setup.get("lt_poller_interval"):
        skip_lt_poller = True
        _LOG.info("Light timer poller interval has not been changed. Skip starting light timer poller task.")

    try:
        if skip_entities is False:
            config.Setup.set("adcp_port", adcp_port)
            config.Setup.set("adcp_timeout", adcp_timeout)
            config.Setup.set("sdap_port", sdap_port)
        if skip_mp_poller is False:
            config.Setup.set("mp_poller_interval", mp_poller_interval)
        if skip_lt_poller is False:
            config.Setup.set("lt_poller_interval", lt_poller_interval)
    except ValueError as v:
        _LOG.error(v)
        return ucapi.SetupError()

    return await complete_setup(skip_entities=skip_entities, skip_mp_poller=skip_mp_poller, skip_lt_poller=skip_lt_poller)



async def complete_setup(skip_entities:bool = False, skip_mp_poller:bool = False, skip_lt_poller:bool = False) -> ucapi.SetupAction:
    """Complete the setup process by creating the entities and starting the poller tasks"""

    try:
        ip = config.Setup.get("ip")
    except ValueError:
        ip = ""

    if not skip_entities:
        try:
            await setup_projector(ip)
        except ConnectionRefusedError:
            return ucapi.SetupError(error_type=ucapi.IntegrationSetupError.CONNECTION_REFUSED)
        except TimeoutError:
            return ucapi.SetupError(error_type=ucapi.IntegrationSetupError.TIMEOUT)
        except ValueError:
            return ucapi.SetupError(error_type=ucapi.IntegrationSetupError.NOT_FOUND)
        except PermissionError:
            return ucapi.SetupError(error_type=ucapi.IntegrationSetupError.AUTHORIZATION_ERROR)
        except Exception:
            return ucapi.SetupError()

        try:
            mp_entity_id = config.Setup.get("id")
            mp_entity_name = config.Setup.get("name")
            rt_entity_id = "remote-"+mp_entity_id
            config.Setup.set("rt-id", rt_entity_id)
            rt_entity_name = mp_entity_name
            config.Setup.set_lt_name_id(mp_entity_id, mp_entity_name)
            lt_entity_id = config.Setup.get("lt-id")
            lt_entity_name = config.Setup.get("lt-name")
        except ValueError as v:
            _LOG.error(v)
            return ucapi.SetupError()

        await media_player.add_mp(mp_entity_id, mp_entity_name)
        await remote.add_remote(rt_entity_id, rt_entity_name)
        await sensor.add_lt_sensor(lt_entity_id, lt_entity_name)

    if config.Setup.get("setup_reconfigure") is True:
    #During the initial setup all needed pollers tasks will be started with the subscribe entities event
        if not skip_mp_poller:
            mp_entity_id = config.Setup.get("id")
            await media_player.MpPollerController.start(mp_entity_id, ip)
        if not skip_lt_poller:
            lt_entity_id = config.Setup.get("lt-id")
            await sensor.LtPollerController.start(lt_entity_id, ip)

    config.Setup.set("setup_complete", True)
    _LOG.info("Setup complete")
    return ucapi.SetupComplete()



async def setup_projector(ip:str = ""):
    """Discovery protector ip if empty. Check if adcp port is open and trigger a test command to check if the adcp password is correct.
    Add all entities to the remote and create poller tasks"""

    try:
        await generate_entity_data(ip)
    except TimeoutError as t:
        _LOG.error(t)
        raise TimeoutError from t
    except ValueError as v:
        _LOG.error(v)
        raise ValueError from t
    except ConnectionRefusedError as r:
        _LOG.error("Connection to projector refused. Please check that the device is reachable from the same network \
as the remote and advertisement and ADCP are activated in the projectors web interface")
        _LOG.error(r)
        raise ConnectionRefusedError from r
    except Exception as e:
        _LOG.error(f"An error occurred while retrieving projector data: {e}")
        raise Exception from e

    adcp_port = config.Setup.get("adcp_port")
    ip = config.Setup.get("ip")

    #Check if adcp port is open
    if not port_check(ip, adcp_port):
        _LOG.error("Timeout while connecting to ADCP port " + str(adcp_port) + " on " + ip)
        _LOG.info("Please check if you entered the correct ip of the projector and ADCP is activated and running on port " + str(adcp_port))
        raise ConnectionRefusedError

    #Check if ADCP password is correct with a test command
    _LOG.info("Sending ADCP test command")
    try:
        await projector.get_light_source_hours(ip)
    except Exception as e:
        error = str(e)
        if error:
            _LOG.error(error)
        _LOG.error("Test command failed")
        raise type(e)(error) from e



async def generate_entity_data(ip:str = ""):
    """Retrieves the ip and data from the projector (serial number & model name).
    Either via the SDAP protocol which can take up to 30 seconds when the default advertisement interval has not been changed
    or via ADCP commands if the ip has been manually entered in the setup
    
    Afterwards this data will be used to generate the entity id and name and sets and stores them to the runtime storage and config file

    :ip: If empty the ip retrieved via SDAP will be used
    """

    if ip == "":
        _LOG.info("Query ip, model name and serial number from projector via SDAP advertisement service")
        _LOG.info("This may take up to 30 seconds when the default advertisement interval has not been changed")

        pjinfo = await projector.projector_def(ip).get_pjinfo()

        if pjinfo is not None:
            _LOG.info("Got data from projector")
            if "serial" and "model" and "ip" in pjinfo:
                if pjinfo["ip"] != "":
                    ip = pjinfo["ip"]
                    _LOG.info("Automatic discovered IP: " + ip)
                    try:
                        config.Setup.set("ip", ip)
                    except Exception as e:
                        raise Exception(e) from e
                else:
                    raise Exception("Got empty ip from projector")

                if pjinfo["model"] or str(pjinfo["serial"]) != "":
                    model = pjinfo["model"]
                    serial = str(pjinfo["serial"])
                else:
                    raise Exception("Got empty model and serial from projector")
            else:
                raise Exception("Missing serial, model and ip in SDAP data")
        else:
            raise Exception("Got no data from projector")
    else:
        _LOG.info("Retrieving model name and serial number via ADCP commands")
        try:
            model_raw = await projector.projector_def(ip).command(ADCP.Get.MODEL)
            serial_raw = await projector.projector_def(ip).command(ADCP.Get.SERIAL)
        except Exception as e:
            raise type(e)(str(e)) from e

        model = model_raw.strip("\"")
        serial = serial_raw.strip("\"")

    entity_id = model + "-" + serial
    entity_name= "Sony " + model

    _LOG.debug("Generated entity ID and name from serial number and model name")
    _LOG.debug("ID: " + entity_id)
    _LOG.debug("Name: " + entity_name)

    try:
        config.Setup.set("id", entity_id)
        config.Setup.set("name", entity_name)
    except Exception as e:
        raise Exception(e) from e

    return True



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
