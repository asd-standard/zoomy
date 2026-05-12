# Changelog

All notable changes to PyZUI will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [0.5.1] - 2026-05-12
### Changed
- GUI integration test restructured from single `gui_integration.py` (1196 lines) to
  `guiintegration/` package with 47+ per-feature test modules, reusable test
  utilities (`qt_simulation`, `scene_helpers`, `image_creation`, `temp_dirs`),
  dedicated `conf.py` and `logger.py`, and `--list-steps`/`--start-step`
  CLI support in main orchestrator
- Documentation massively expanded: added new rst modules for backup, config,
  logger, objects, tilesystem, windows, and converters subsystems; major
  restructuring and expansion of objectsystem, tiledmediaobject, tilingsystem,
  windowsystem, convertersystem, projectstructure docs; new SVG and string
  rendering ecosystem reference documentation; new SVG features usage guide
- Logger system: `LoggerConfig.initialize()` now re-entrant for runtime
  reconfiguration; `log_dir` supports tilde expansion (`~/logs`);
  `LOGGING.md` reference guide created

## [0.5.0] - 2026-05-10
### Added
- Configuration management system (ConfigManager) with JSON config files,
  validation, merge overrides, and example config (`pyzui_config_example.json`)
- Autosave/backup system with per-scene directories, configurable interval,
  rotation, and expiration; AutosaveSettingsDialog for user control
- Zoom limits manager to prevent crashes at extreme zoom levels;
  ZoomSettingsDialog for user control
- SVG elongation: interactive resizing of arrows (Ctrl+Wheel), squares, circles,
  triangles, and sticks via mouse wheel with modifier keys
- SVG caching system for embedded SVGs with startup cache cleanup
- Copy/paste support within scenes (Ctrl+C / Ctrl+V) via SceneClipboardManager
- Import scene from file (appends to current scene)
- New tab / close tab for managing multiple scenes independently
- Render order toggle: switch between smaller-on-top and larger-on-top via View
  menu (Ctrl+R) or `render.order` config key (`smaller_on_top` / `larger_on_top`)
- Parallel text rendering for improved zoom performance (SceneParallelRenderer)
  with priority-based batcher for worker pool tasks
- Version bump utility script (`scripts/bump_version.py`) with automatic
  home.png screenshot capture after version update
- Embedded SVG support in scene (.pzs) files
- Application icon loading
- Comprehensive command-line arguments: autosave control (interval, max backups,
  expire days, disable), zoom defaults, cleanup control, logging flags
- Build configuration (`pyproject.toml`) and pre-commit hooks (ruff linter +
  formatter)
- Launcher script (`pyzui.sh`) with conda environment integration
- AGENTS.md agent guidelines for AI-assisted development
- Shutdown orchestration: unified thread cleanup before Qt destruction
- SVG picker and modifier dialog windows
- Scene selection persistence across save/load
- New SVG and image data assets in data/SVG/

### Changed
- `main.py` fully rewritten with ConfigManager, CL argument processing,
  proper shutdown flow
- Scene constructor now accepts configuration dict (autosave, render order,
  zoom settings)
- Scene module refactored: utilities extracted to `sceneutils/` (autosave,
  clipboard, parallel renderer, priority batcher)
- Object utilities extracted to `objectsutils/` with `ZoomManager` class
- `QZUI` constructor expanded (config, autosave_config parameters; default
  framerate 10→20; default zoom sensitivity 10→50)
- `Scene.render()` rewritten with parallel rendering support and sort optimization
- Import organization standardized across all modules (stdlib → third-party
  → local)
- Comprehensive type annotations added across all modules
- Docstrings rewritten and expanded across all modules
- `pyzui/__init__.py` `__all__` flattened (removed hierarchical nesting)

### Fixed
- Thread safety: `__objects_lock` consistently used for all scene object iteration
- Qt threading errors during Python garbage collection (proper `__del__` cleanup)
- Autosave timer properly stopped on scene replacement to prevent log noise
- Focus out event resets keyboard modifiers and rectangle drawing state

### Removed
- `data/02_green_gradient.png` and `data/06_cyan_circles.png` (replaced with
  new data/SVG/ assets)
- `test/unittest/.coverage` file from git tracking
- SVGRectangle module (replaced with dedicated SVG elongation utilities)

## [0.4.0] - 2026-03-03
### Added
- Process pooling system for tiler object calls
- Thread pooling system for tiler tile creation loop (`__load_row_from_file`)
- Comprehensive integration tests for concurrent stress
- Tiler runner module with parallel execution support

## [0.3.2] - 2026-02-27
### Added
- Mediaobject bulk selection via control-click / left-click drag
- GUI integration test for bulk selection behavior
### Fixed
- Lazy attribute resolution edge case
### Removed
- Dead thread inheritance from converter classes

## [0.3.1] - 2026-02-24
### Added
- Comprehensive logging integration tests
- Comprehensive logger unit tests
### Fixed
- Logging: `set_level()` now updates all handlers, console enabled by default
- Split-loop bug in string mediaobject processing
- Cache invalidation after `modifyStringMediaObject` call
- Color selection logic in UI dialogs

## [0.3.0] - 2026-02-20
### Added
- Hybrid rendering system for StringMediaObject (CPU-efficient caching)
### Changed
- Rendering pipeline for text objects now uses cached QImages

## [0.2.2] - 2026-02-18
### Changed
- Renamed `converter_runner` module to `converterrunner`
- Moved tilestore cleanup to application shutdown for faster startup
### Added
- Comprehensive type annotations for all tilesystem modules
- Comprehensive type annotations for all windows module classes

## [0.2.1] - 2026-01-16
### Added
- File extension filter in Open Media Directory dialog
- PDF size limit validation in Open Media Directory
### Fixed
- Pytest hang: changed default multiprocessing context to `fork`
- Auto-detect safe multiprocessing context based on thread state
### Removed
- `__pycache__` files from git tracking

## [0.2.0] - 2026-01-10
### Added
- Process-based parallel conversion for converters (ProcessPoolExecutor, `spawn` context)
- `converter_runner` module with `ConversionHandle` progress tracking
- Pause/resume mechanism for TileProvider and TileManager
### Changed
- TiledMediaObject conversion now uses process-based parallelism instead of threads
### Removed
- `disk_lock` from PDFConverter (no longer needed with process isolation)
- `test_converter_pipeline.py` (replaced with integration test)

## [0.1.5] - 2026-01-07
### Added
- `ModifyTiledMediaObjectDialog` for image manipulation
- Unit test for render order verification
- Integration tests for save/load round-trip scene preservation
### Fixed
- Rendering order: smaller objects now render on top of larger ones (reversed z-order)
- Selection now returns topmost (smallest) object at click position
- Scene loading: `autofit=False` to preserve saved zoomlevel from `.pzs` files

## [0.1.4] - 2025-12-16
### Added
- GitHub Actions CI workflow for Sphinx documentation
- README.md with project description and contribution guidelines
### Fixed
- Sphinx documentation warnings
- Code quality warnings identified by pyflakes
### Changed
- Restructured documentation into logical sections (getting started, technical, testing)
- Reorganized project files into standard layout

## [0.1.3] - 2025-11-19
### Added
- Sphinx documentation system with autodoc support
- Documentation for all core modules (19+ modules documented)
- Scene class documentation expanded
### Changed
- Updated magickconverter, pdfconverter, and tiler with code improvements

## [0.1.2] - 2025-10-28
### Removed
- Old LaTeX documentation (`doc/` directory including manual.tex)
- `COPYING.txt` (replaced with GPLv3 license header)
### Changed
- Updated `__init__.py` metadata (author, maintainer, license fields)

## [0.1.1] - 2025-05-29
### Added
- Dialog windows system for user interaction
### Changed
- Major restructure: moved all modules into `pyzui/` package
- MainWindow and QZUI widget refinements
- MediaObject class hierarchy improvements

## [0.1.0] - 2025-03-13
### Added
- Initial release with Zooming User Interface framework
- Tile system: tile cache, tile manager, tile providers (static, dynamic, OSM, Mandelbrot, fern)
- Media object types: tiled media, string media, SVG media
- Scene management with object sorting (`__sort_objects`)
- Converter system: VIPS, PDF, ImageMagick converters
- PPM image format support
- Tile store with persistent caching
