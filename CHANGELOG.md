# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

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
