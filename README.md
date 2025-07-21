# Sony Projector ADCP integration for Unfolded Circle Remote Devices <!-- omit in toc -->

## ⚠️ Disclaimer ⚠️ <!-- omit in toc -->

This software may contain bugs that could affect system stability. Please use it at your own risk!

## <!-- omit in toc -->

Integration for Unfolded Circle Remote Devices running [Unfolded OS](https://www.unfoldedcircle.com/unfolded-os) (currently Remote Two and [Remote 3](https://www.unfoldedcircle.com)) to control Sony projectors that support the ADCP protocol.

Using [uc-integration-api](https://github.com/aitatoi/integration-python-library).

## Table of Contents <!-- omit in toc -->

- [Usage](#usage)
  - [Supported models](#supported-models)
  - [Projector Setup](#projector-setup)
    - [ADCP Authentication](#adcp-authentication)
    - [Activate ADCP \& Advertisement (SDAP)](#activate-adcp--advertisement-sdap)
  - [Advanced setup settings](#advanced-setup-settings)
- [Entities](#entities)
- [Commands \& attributes](#commands--attributes)
  - [Supported media player commands](#supported-media-player-commands)
  - [Supported media player attributes](#supported-media-player-attributes)
  - [Supported simple commands (media player \& remote entity)](#supported-simple-commands-media-player--remote-entity)
  - [Supported remote entity commands](#supported-remote-entity-commands)
  - [Default remote entity button mappings](#default-remote-entity-button-mappings)
  - [Attributes poller](#attributes-poller)
    - [Media player](#media-player)
    - [Health status poller](#health-status-poller)
- [Installation](#installation)
  - [Run on the remote as a custom integration driver](#run-on-the-remote-as-a-custom-integration-driver)
    - [Limitations / Disclaimer](#limitations--disclaimer)
      - [Missing firmware features](#missing-firmware-features)
    - [1 - Download integration driver](#1---download-integration-driver)
    - [2 - Upload \& installation](#2---upload--installation)
      - [Upload in Web Configurator](#upload-in-web-configurator)
      - [Alternative - Upload via Core API or 3rd party tools](#alternative---upload-via-core-api-or-3rd-party-tools)
  - [Run on a separate device as an external integration](#run-on-a-separate-device-as-an-external-integration)
    - [Remote requirements](#remote-requirements)
    - [Bare metal/VM](#bare-metalvm)
    - [Requirements](#requirements)
      - [Start the integration](#start-the-integration)
    - [Docker container](#docker-container)
- [Build](#build)
  - [Build distribution binary](#build-distribution-binary)
    - [x86-64 Linux](#x86-64-linux)
    - [aarch64 Linux / Mac](#aarch64-linux--mac)
  - [Create tar.gz archive](#create-targz-archive)
- [Versioning](#versioning)
- [Changelog](#changelog)
- [Resources](#resources)
  - [ADCP protocol manual](#adcp-protocol-manual)
  - [ADCP supported commands list](#adcp-supported-commands-list)
- [Planned improvements](#planned-improvements)
- [Credits](#credits)
- [Contributions](#contributions)
- [License](#license)

## Usage

### Supported models

Most Sony home cinema projectors with an Ethernet RJ-45 port that were released since 2016 should be supported. Please refer to Sony's user manual for more details.

For a full list of all supported ADCP commands by your model see [ADCP Supported commands list](#adcp-supported-commands-list).

If your model is older or not supported you can try to use the deprecated [Sony SDCP integration](https://github.com/kennymc-c/ucr2-integration-sonySDCP)

### Projector Setup

You need to either assign a static ip address to your projector or configure your router's dhcp server to always assign the same ip address to the projector. This is due to a technical limitation on how the SDAP advertisement protocol used by Sony projectors works.

You may need to activate the WebUI and network management in the projector menu first to configure the following settings and be able to turn on the projector remotely.

#### ADCP Authentication

Authentication for ADCP is enabled by default on most models. Therefore it's required to enter the WebUI password of the projector in the integration setup. Leave the field empty if you disabled authentication.

**Important note: If you ever change the hostname of the device the integration is running on or use a configuration file that was created with on a different host, you need to reconfigure the projector in the integration setup.**

#### Activate ADCP & Advertisement (SDAP)

On most projectors ADCP and Advertisement via SDAP is turned on by default. Please refer to Sony's user manual on how to turn these services on manually as there are different variants of the projector WebUI depending on the model you are using.

### Advanced setup settings

If you're using different ports for ADCP or SDAP advertisement than the default values, you need to activate the advanced settings option when configuring the integration. Here you can change the ADCP/SDAP ports and timeout as well as the interval of both poller intervals.

Please note that when running this integration on the remote the power/mute/input poller interval is always set to 0 to deactivate this poller in order to reduce battery consumption and save cpu/memory usage.

## Entities

- Media player
  - Source select feature to choose the input from a list
  - Shows video signal infos in the media widget. Tap the refresh symbol to update the widget or use the UPDATE_VIDEO_INFO command
- Remote
  - Pre-defined buttons mappings and ui pages with all available commands that can be customized in the web configurator
  - Send native ADCP commands via the send command and send command sequence command (useful for commands thats are not available as simple commands)
  - Use command sequences in the activity editor instead of creating a macro for each sequence. All command names have to be in upper case and separated by a comma
  - Support for repeat, delay and hold
    - Hold just repeats the command continuously for the given hold time. There is no native hold function for the ADCP protocol as with some ir devices to activate additional functions
- Sensors
  - Health sensors
    - Light source timer
    - Temperature
      - The sensor will only be added as available entity if your model can provide temperature data
    - System status (error and warning messages from the projector)
    - All health sensors will be updated every time the projector is powered on or off by the remote and automatically every 30 minutes (can be changed in the advanced setup) while the projector is powered on and the remote is not in sleep/standby mode or the integration is disconnected
  - Video signal
    - Shows the current resolution, framerate, dynamic range format, color space, color format and 2D/3D status
    - Video signal data is automatically updated when the projector or video muting is turned on or off and when the input is changed

## Commands & attributes

### Supported media player commands

- Turn On/Off/Toggle
- Mute/Unmute/Toggle
  - Used for picture muting
- Cursor Up/Down/Left/Right/Enter/Back
  - The back command is also mapped to cursor left as there is no separate back command for the projector. Inside the setup menu cursor left has the same function as a typical back command
- Home & Menu
  - Opens the setup menu
- Source Select
  - HDMI 1, HDMI 2

### Supported media player attributes

- Power Status (On, Off, Unknown)
- Muted (True, False)
- Source
- Source List (HDMI 1, HDMI 2)

### Supported simple commands (media player & remote entity)

- Input HDMI 1 & 2
  - Intended for the remote entity in addition to the source select feature of the media player entity
- Calibration Presets*
  - Cinema Film 1, Cinema Film 2, Reference, TV, Photo, Game, Bright Cinema, Bright TV, User
- Aspect Ratios* ***
  - Normal, Squeeze, Stretch**, V Stretch, Zoom 1:85, Zoom 2:35
- Picture Positions (Select and Save)***
  - 1,85, & 2,35***
  - Custom 1-3
  - Custom 4 & 5***
- HDR* ***
  - On, Off, Auto
- HDR Dynamic Tone Mapping* ***
  - Mode 1, 2, 3, Off
- Lamp Control* ***
  - High, Low
- Laser Dimming* ***
  - Up, Down
- Dynamic Iris/Light Source Control * ***
  - Off, Full, Limited
- Motionflow*
  - Off, Smooth High, Smooth Low, Impulse\*\*\*, Combination\***, True Cinema
- 2D/3D Display Select** ***
  - 2D, 3D, Auto
- 3D Format** ***
  - Simulated 3D, Side-by-Side, Over-Under
- Input Lag Reduction*
  - On, Off
- Menu Position
  - Bottom Left, Center
- Lens Control***
  - Lens Shift Up/Down/Left/Right
  - Lens Focus Far/Near
  - Lens Zoom Large/Small
- Update Health & Video signal info
  - This can be used in macros or command sequences together with commands of your media playback devices where the video signal may get changed or updated (e.g. play, pause, enter/select)

\* _Only works if a video signal is present at the input_ \
\** _May not work work with all video signals. Please refer to Sony's user manual_ \
\*** _May not work on certain projector models that do not support this mode/feature. Please refer to Sony's user manual_

If a command can't be processed or applied by the projector this will result in a bad request error on the remote. The response error message from the projector is shown in the integration log

### Supported remote entity commands

- On, Off, Toggle
- Send command
  - Simple command names have to be in upper case
- Send command sequence
  - Simple command names have to be in upper case and separated by a comma

You can also send native ADCP commands with the send command and send command sequence commands. This is useful for commands that are not available as simple commands or need a specific value. Please refer to the [ADCP supported commands list](#adcp-supported-commands-list) for a list of all commands for your projector model.

### Default remote entity button mappings

_The default button mappings and ui pages can be customized in the web configurator._

| Button                  | Short Press command | Long Press command |
|-------------------------|---------------------|--------------------|
| BACK                    | Cursor Left | |
| HOME                    | Menu |  |
| VOICE                   | | |
| VOLUME_UP/DOWN          | | |
| MUTE                    | Toggle Picture Muting | |
| DPAD_UP/DOWN/LEFT/RIGHT | Cursor Up/Down/Left/Right | |
| DPAD_MIDDLE             | Cursor Enter |  |
| GREEN                   |              |  |
| YELLOW                  |              |  |
| RED                     |              |  |
| BLUE                    |              |  |
| CHANNEL_UP/DOWN         | Input HDMI 1/2 |  |
| PREV                    | |  |
| PLAY                    | |  |
| NEXT                    | |  |
| POWER                   | Power Toggle |  |

### Attributes poller

#### Media player

By default the integration checks the status of all media player entity attributes **every 20 seconds** while the remote is not in standby/sleep mode or disconnected from the integration. The interval can be changed in the advanced settings. Set it to 0 to deactivate this function. **When running on the remote as a custom integration the interval will be automatically set to 0 to reduce battery consumption and save cpu/memory usage.**

#### Health status poller

All health sensor data (light source timer, temperature and error/warning) will be updated every time the projector is powered on or off by the remote and automatically **every 30 minutes by default while the projector is powered on** and the remote is not in sleep/standby mode or the integration is disconnected. The interval can be changed in the advanced settings.

## Installation

### Run on the remote as a custom integration driver

#### Limitations / Disclaimer

_⚠️ This feature is currently only available in beta firmware releases and requires version 1.9.2 or newer. Please keep in mind that due to the beta status there are missing firmware features that require workarounds (see below)._

##### Missing firmware features

- The configuration file of custom integrations are not included in backups.
- You currently can't update custom integrations. You need to delete the integration from the integrations menu first and then re-upload the new version. Do not edit any activity or macros that includes entities from this integration after you removed the integration and wait until the new version has been uploaded and installed. You also need to add re-add entities to the main pages after the update as they are automatically removed. An update function will probably be added once the custom integrations feature will be available in stable firmware releases.

#### 1 - Download integration driver

Download the uc-intg-sonyadcp-x.x.x-aarch64.tar.gz archive in the assets section from the [latest release](https://github.com/kennymc-c/ucr2-integration-sonyADCP/releases/latest).

#### 2 - Upload & installation

##### Upload in Web Configurator

Since firmware version 2.2.0 you can upload custom integrations in the web configurator. Go to _Integrations_ in the top menu, on the top right click on _Add new/Install custom_ and choose the downloaded tar.gz file.

##### Alternative - Upload via Core API or 3rd party tools

```shell
curl --location 'http://$IP/api/intg/install' \
--user 'web-configurator:$PIN' \
--form 'file=@"uc-intg-sonyadcp-$VERSION-aarch64.tar.gz"'
```

There is also a Core API GUI available at https://_Remote-IP_/doc/core-rest. Click on Authorize to log in (username: web-configurator, password: your PIN), scroll down to POST intg/install, click on Try it out, choose a file and then click on Execute.

Alternatively you can also use the unofficial [UC Remote Toolkit](https://github.com/albaintor/UC-Remote-Two-Toolkit)

### Run on a separate device as an external integration

#### Remote requirements

- Firmware 1.7.12 or newer to support simple commands and remote entities

#### Bare metal/VM

#### Requirements

- Python 3.11
- Install Libraries:  
  (using a [virtual environment](https://docs.python.org/3/library/venv.html) is highly recommended)

```shell
pip3 install -r requirements.txt
```

##### Start the integration

```shell
python3 intg-sonyadcp/driver.py
```

#### Docker container

For the mDNS advertisement to work correctly it's advised to start the integration in the host network (`--net=host`). You can also set the websocket listening port with the environment variable `UC_INTEGRATION_HTTP_PORT`, set the listening interface with `UC_INTEGRATION_INTERFACE` or change the default debug log level with `UC_LOG_LEVEL`. See available [environment variables](https://github.com/unfoldedcircle/integration-python-library#environment-variables)
in the Python integration library.

All data is mounted to `/usr/src/app`:

```shell
docker run --net=host -n 'ucr2-integration-sonyadcp' -v './ucr2-integration-sonyADCP':'/usr/src/app/':'rw' 'python:3.11' /usr/src/app/docker-entry.sh
```

## Build

Instead of downloading the integration driver archive from the release assets you can also build and create the needed distribution binary and tar.gz archive yourself.

For Python based integrations Unfolded Circle recommends to use `pyinstaller` to create a distribution binary that has everything in it, including the Python runtime and all required modules and native libraries.

### Build distribution binary

First we need to compile the driver on the target architecture because `pyinstaller` does not support cross compilation.

The `--onefile` option to create a one-file bundled executable should be avoided:

- Higher startup cost, since the wrapper binary must first extract the archive.
- Files are extracted to the /tmp directory on the device, which is an in-memory filesystem.  
  This will further reduce the available memory for the integration drivers!

We use the `--onedir` option instead.

#### x86-64 Linux

On x86-64 Linux we need Qemu to emulate the aarch64 target platform:

```bash
sudo apt install qemu binfmt-support qemu-user-static
docker run --rm --privileged multiarch/qemu-user-static --reset -p yes
```

Run pyinstaller:

```shell
docker run --rm --name builder \
    --platform=aarch64 \
    --user=$(id -u):$(id -g) \
    -v "$PWD":/workspace \
    docker.io/unfoldedcircle/r2-pyinstaller:3.11.6-0.2.0  \
    bash -c \
      "cd /workspace && \
      python -m pip install -r requirements.txt && \
      pyinstaller --clean --onedir --name int-sonyadcp intg-sonyadcp/driver.py"
```

#### aarch64 Linux / Mac

On an aarch64 host platform, the build image can be run directly (and much faster):

```shell
docker run --rm --name builder \
    --user=$(id -u):$(id -g) \
    -v "$PWD":/workspace \
    docker.io/unfoldedcircle/r2-pyinstaller:3.11.6-0.2.0  \
    bash -c \
      "cd /workspace && \
      python -m pip install -r requirements.txt && \
      pyinstaller --clean --onedir --name intg-sonyadcp intg-sonyadcp/driver.py"
```

### Create tar.gz archive

Now we need to create the tar.gz archive that can be installed on the remote and contains the driver.json metadata file and the driver distribution binary inside the bin directory

```shell
mkdir -p artifacts/bin
mv dist/intg-sonyadcp/* artifacts/bin
mv artifacts/bin/intg-sonyadcp artifacts/bin/driver
cp driver.json artifacts/
tar czvf uc-intg-sonyadcp-aarch64.tar.gz -C artifacts .
rm -r dist build artifacts intg-sonyadcp.spec
```

## Versioning

I use [SemVer](http://semver.org/) for versioning. For the versions available, see the
[tags and releases in this repository](https://github.com/kennymc-c/ucr2-integration-sonyADCP/releases).

## Changelog

The major changes found in each new release are listed in the [changelog](CHANGELOG.md)
and under the GitHub [releases](/releases).

## Resources

### ADCP protocol manual

[https://pro.sony/s3/2018/07/05125823/Sony_Protocol-Manual_1st-Edition.pdf](https://pro.sony/s3/2018/07/05125823/Sony_Protocol-Manual_1st-Edition.pdf)

### ADCP supported commands list

- VPL models: [https://community.jeedom.com/uploads/short-url/90hLTY2VlQjjwLJoVjX5BQ6U3dZ.pdf](https://community.jeedom.com/uploads/short-url/90hLTY2VlQjjwLJoVjX5BQ6U3dZ.pdf)
- GTZ models: [https://www.sony.com/electronics/support/res/manuals/9976/42368d260676e4dc154f00932c23e5f0/99769555M.pdf](https://www.sony.com/electronics/support/res/manuals/9976/42368d260676e4dc154f00932c23e5f0/99769555M.pdf)

If your projector is not listed in the supported commands list please contact your authorized Sony dealer to get the full ADCP supported commands list document for your projector model.

## Planned improvements

- Use multicast SDDP (Simple Device Discovery Protocol) for advertisement instead of SDAP which has limitations

## Credits

SDAP advertisement concept adapted from: [Galala7/pySDCP](https://github.com/Galala7/pySDCP)

ADCP concept adapted from:
[Sony ADCP Home Assistant Custom Component by tokyotexture](https://github.com/tokyotexture/homeassistant-custom-components/blob/master/switch/SONY_ADCP.py)

## Contributions

Contributions to add new feature, implement #TODOs from the code or improve the code quality and stability are welcome! First check whether there are other branches in this repository that maybe already include your feature. If not, please fork this repository first and then create a pull request to merge your commits and explain what you want to change or add.

## License

This project is licensed under the [**GNU GENERAL PUBLIC LICENSE**](https://choosealicense.com/licenses/gpl-3.0/).
See the [LICENSE](LICENSE) file for details.
