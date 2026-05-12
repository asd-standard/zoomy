# PyZUI Logging System

This document describes the new centralized logging system for PyZUI.

## Overview

The logging system provides:
- **Centralized configuration** - Single point to control all logging
- **Multiple log levels** - DEBUG, INFO, WARNING, ERROR, CRITICAL
- **Flexible output** - Console and/or file logging
- **Color-coded console** - Easy visual identification of log levels
- **Rotating log files** - Automatic log file rotation (10 MB max, 5 backups)
- **Runtime control** - Enable/disable debug mode during execution

## Quick Start

### Running with Debug Mode

```bash
# Enable debug mode (maximum logging detail)
python main.py --debug

# Enable verbose mode (detailed info, less than debug)
python main.py --verbose

# Run normally (warnings and errors only)
python main.py
```

### Command-Line Options

```bash
python main.py [options]

Options:
  -d, --debug           Enable debug mode (maximum logging detail)
  -v, --verbose         Enable verbose mode (detailed info logging)
  --config FILE         Load settings from config file (JSON)
  --log-dir DIR         Directory for log files (default: ./logs)
  --no-console          Disable console logging
  --no-file             Disable file logging
  --no-color            Disable colored console output
  -h, --help            Show help message
```

### Examples

```bash
# Debug mode with custom log directory
python main.py --debug --log-dir /tmp/pyzui-logs

# Verbose mode with file logging only (no console output)
python main.py --verbose --no-console

# Normal mode with no colored output
python main.py --no-color

# Load settings from config file
python main.py --config pyzui_config.json
```

## Configuration File

You can configure logging via a JSON configuration file:

```json
{
  "logging": {
    "debug": false,
    "verbose": false,
    "log_to_file": true,
    "log_to_console": true,
    "colored_output": true,
    "log_dir": "logs"
  }
}
```

Save this as `pyzui_config.json` and run:
```bash
python main.py --config pyzui_config.json
```

## Log Levels

The logging system uses standard Python logging levels:

| Level    | Description                                      | When to Use                          |
|----------|--------------------------------------------------|--------------------------------------|
| DEBUG    | Detailed diagnostic information                  | Development and troubleshooting      |
| INFO     | General informational messages                   | Tracking normal application flow     |
| WARNING  | Warning messages for potentially harmful events  | Default level for normal operation   |
| ERROR    | Error messages for serious problems              | Always shown                         |
| CRITICAL | Critical errors causing application failure      | Always shown                         |

### Console vs File Logging Levels

By default:
- **Console**: Shows WARNING and above (normal mode), INFO and above (verbose), or everything (debug)
- **File**: Always captures DEBUG and above for comprehensive logging

## Log File Location

Log files are stored in the `logs/` directory by default:
- Main log: `logs/pyzui.log`
- Rotated logs: `logs/pyzui.log.1`, `logs/pyzui.log.2`, etc.

Each log file has a maximum size of 10 MB, and up to 5 backup files are kept.

## Using Logging in Your Code

### For New Modules

```python
from pyzui.logger import get_logger

class MyClass:
    def __init__(self):
        self.logger = get_logger('MyClass')

    def my_method(self):
        self.logger.debug('Entering my_method')
        self.logger.info('Processing data')
        self.logger.warning('Something might be wrong')
        self.logger.error('An error occurred')
        self.logger.critical('Critical failure!')
```

### Runtime Control

You can enable/disable debug mode at runtime:

```python
from pyzui.logger import LoggerConfig

# Enable debug mode during execution
LoggerConfig.enable_debug()

# Disable debug mode
LoggerConfig.disable_debug()

# Set specific log level
import logging
LoggerConfig.set_level(logging.INFO)
```

## Log Format

### Console Output
```
[LEVEL   ] ModuleName               | Message
```

Example:
```
[INFO    ] main                      | Starting PyZUI application
[DEBUG   ] TileManager               | Initializing tile cache
[WARNING ] Scene                     | Object out of bounds
[ERROR   ] Converter.myimage.jpg     | Conversion failed
```

### File Output
```
YYYY-MM-DD HH:MM:SS | [LEVEL   ] | ModuleName               | FunctionName         | Message
```

Example:
```
2025-11-30 14:23:45 | [INFO    ] | main                      | main                 | Starting PyZUI application
2025-11-30 14:23:45 | [DEBUG   ] | TileManager               | init                 | Initializing tile cache
```

## Color Coding (Console)

When colored output is enabled:
- **DEBUG**: Cyan
- **INFO**: Green
- **WARNING**: Yellow
- **ERROR**: Red
- **CRITICAL**: Magenta

## Troubleshooting

### Problem: No logs appearing

**Solution**: Check that logging is initialized. The main.py should automatically initialize logging, but if using PyZUI as a library:

```python
from pyzui.logger import LoggerConfig

LoggerConfig.initialize(debug=True)
```

### Problem: Too much output in console

**Solution**: Run without --debug or --verbose flags, or use --no-console:

```bash
python main.py  # Only warnings and errors
python main.py --no-console  # No console output, file only
```

### Problem: Can't find log files

**Solution**: Check the log directory:

```python
from pyzui.logger import LoggerConfig

print(f"Log file: {LoggerConfig.get_log_file_path()}")
```

Or specify a custom directory:
```bash
python main.py --log-dir /path/to/logs
```

## Advanced Usage

### Per-Module Log Levels

```python
from pyzui.logger import LoggerConfig
import logging

# Set debug level only for TileManager
LoggerConfig.set_level(logging.DEBUG, module='TileManager')
```

### Disable File Logging for Performance

```bash
python main.py --no-file
```

This can improve performance slightly by eliminating disk I/O for logging.

## Migration Notes

The old logging system used:
```python
import logging
self.__logger = logging.getLogger("ModuleName")
```

The new system uses:
```python
from pyzui.logger import get_logger
self.__logger = get_logger("ModuleName")
```

All existing logger calls (`.debug()`, `.info()`, `.warning()`, `.error()`, `.critical()`) work exactly the same way.

## Best Practices

1. **Use appropriate log levels**:
   - `DEBUG`: Detailed diagnostic information
   - `INFO`: Confirmation that things are working as expected
   - `WARNING`: Something unexpected happened, but the application continues
   - `ERROR`: A serious problem occurred
   - `CRITICAL`: The application may be unable to continue

2. **Include context in messages**:
   ```python
   # Good
   logger.debug(f'Loading tile {tile_id} from {path}')

   # Bad
   logger.debug('Loading tile')
   ```

3. **Use exceptions for errors**:
   ```python
   try:
       result = risky_operation()
   except Exception as e:
       logger.exception(f'Failed to perform operation: {e}')
   ```

4. **Don't log in tight loops** (use sparingly):
   ```python
   # Avoid
   for i in range(1000000):
       logger.debug(f'Processing item {i}')

   # Better
   logger.info(f'Processing {len(items)} items')
   for i, item in enumerate(items):
       if i % 10000 == 0:
           logger.debug(f'Progress: {i}/{len(items)}')
   ```

## Support

For issues or questions about the logging system, please check the logs first:
```bash
# View recent logs
tail -f logs/pyzui.log

# Search for errors
grep ERROR logs/pyzui.log
```
