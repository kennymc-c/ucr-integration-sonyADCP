# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [1.5.0] - 2026-02-28

### ⚠️ Known issue

- If random sensor and/or select entities are suddenly shown as unavailable after a restart please run the setup for the affected device again without changing anything. For Docker setups you can also stop and restart the integration.

### ⚠️ Breaking

- Removed video signal infos from media player playback attributes as sensors can be added as widgets to activities since firmware 2.7.2. Please use the video sensor instead
- If you are running the integration externally (e.g. Docker) you need to delete config.json and run the setup again
  - Don't panic: No entity ids have been changed!
- Renamed `UPDATE_SETTING_SENS` simple command to `UPDATE_ALL_SENSORS` as it now updates all sensors and not only some of them
  - This requires re-mapping this command in activities and macros

### Added

- Added 20 select entities (if the setting is supported by your model):
  - This needs firmware 2.8.3 or never
  - Available and current options will be updated when the projector is powered on or off, the input is changed, picture is muted muted or when a send command/send command sequence command from the remote entity has been received
    - Use the `UPDATE_SELECT_OPTION` simple command to update all sensors manually
- Added sensors for input and laser/iris brightness
  - Iris brightness has not been tested with a supported model. Therefore the value shown by the sensor may not match the one in the projector menu. Please report any issues with the iris brightness sensor so these can be fixed
- Added simple commands for iris brightness and contrast/dynamic HDR enhancer
  - Iris brightness has not been tested with a supported model. Therefore the up/down intervals might be too big/small. Currently it uses the same scale and interval as laser brightness. Please report any issues with the iris brightness command so these can be fixed

### Fixed

- Fixed remote entity power state not updating
- Fixed pictures mode button positions on remote user interface page
- Fixed device class of binary sensors

### Changed

- Internal code cleanup, simplification and type-safe measurements
- Removed entity ids and names from config file and generate them at startup to prevent large configuration files
- Updated ucapi Python library to 0.5.2
- Updated UC r2-pyinstaller image in build workflow to 3.11.13-0.5.0
- Updated upload/download build actions

## [1.4.1] - 2026-01-24

### Fixed

- Fixed an issue where some sensors are shown as unavailable after a restart of the integration/remote

### Changed

- Improved log level filters when running under systemd like on the remote

### Added

- Added sensors for gamma, color space and color temperature
  - These sensors will be updated either with the global `UPDATE_SETTING_SENS` simple command or if a send command/send command sequence command has been received which allows you to send raw ADCP commands like changing these settings. There are no dedicated simple commands to change gamma, color space and temperature

## [1.4.0] - 2026-01-05

### Added

- Added 15 setting sensors for almost all settings
  - Please power on the projector during setup as most sensor values can't be retrieved when the device is powered off
    - Otherwise the sensor value will be shown as temporarily unavailable and updated once the projector is powered on
    - You can also manually update all setting sensors at once with a dedicated simple command
  - If a setting is not supported by the projector model the corresponding sensor is not added as available entity
  - Sensors for laser dimming and lens control are not included as their current values can't be polled through ADCP
- Added missing HDR mode commands for HDR10, HDR Reference and HLG
- Added missing Picture Preset commands for User 1-3
- Added debug log messages for websocket connect/disconnect events

### Fixed

- Fixed issue where media player attributes were not updated in some situations ([#3](https://github.com/kennymc-c/ucr-integration-sonyADCP/issues/3))

### Changed

- Updated GitHub actions in build workflow
- Updated UC Python library to 0.5.1

## [1.3.1] - 2025-11-10

### Fixed

- Fixed non working status update of the remote entity
- Fixed wrong status update when using the toggle command

### Changed

- Updated UC Python library to 0.3.2
- Updated pyinstaller build image to 3.11.13-0.4.0

## [1.3.0] - 2025-08-20

### Breaking Changes

- Changed the default remote entity name and the entity id for the light source timer sensor
  - Please re-run the setup when running as an external integration (e.g. via Docker)

### Fixed

- Fixed a timeout while sending an on/off/toggle command ([#2](https://github.com/kennymc-c/ucr-integration-sonyADCP/issues/2))
- Fixed handling of non supported query commands used for the video signal sensor/media playback attributes
- Fixed wrong English sensor names

### Changed

- Improved handling of updating attributes for entities that have not been added as configured entities

## [1.2.0] - 2025-07-21

### Fixed

- Fixed wrong mapping of dynamic light control limited command in remote entity

### Added

- Added a video signal sensor that shows the current resolution, framerate, dynamic range format, color space, color format and 2D/3D status
  - Video signal data is automatically updated when the projector or video muting is turned on or off and when the input is changed
- Added video signal infos (see above) as media playback attributes (artist and title) to show them in activities within the media widget as sensors can't be added to activities
  - If you tap on the refresh icon in the media widget the data is updated
- Added a projector temperature and a system status sensor to show error and warning messages
  - The sensor will only be added as available entity if your model can provide temperature data
  - All health sensors (light source timer, temperature and error/warning) will automatically be updated by the health status poller (see below) and when the projector is turned on or off
- Added simple commands to manually update video signal infos and all health status sensors (light source timer, temperature and error/warning) in both sensors and media playback attributes
  - This can be used in macros or command sequences together with commands of your media playback devices where the video signal may get changed or updated (e.g. play, pause, enter/select)

### Changed

- Renamed the light source timer poller task to health status poller task because it now also polls temperature, error and warning messages

## [1.1.2] - 2025-06-06

### Changed

- Updated ucapi dependency to 0.3.1

### Fixed

- Fixed non working picture position save commands

## [1.1.1] - 2025-04-25

### Fixed

- Fixed missing MODE_HDR_TONEMAP_3 simple command due to a duplicated command name for mode 2

### Changed

- Updated pyinstaller build image to r2-pyinstaller:3.11.12-0.3.0
- Updated dependencies

## [1.1.0] - 2025-04-19

### Breaking Changes

- The integration now support multiple devices. As the configuration file format has changed existing installations have to be reconfigured

### Added

- Added picture position save commands

### Fixed

- Fixed select source command in media player entity not working
- Shortened or renamed some simple commands that exceeded the 20 character limit

## [1.0.0] - 2025-04-05

First release
