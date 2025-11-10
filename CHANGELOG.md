# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

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
