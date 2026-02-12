# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

This is an **eNose MPW2 Log Analyzer** - a sensor data analysis tool built with PySide6 and PyQtGraph. The application analyzes log files from gas sensors, providing multi-axis visualization and statistical analysis for capacitance, temperature, humidity, oscillator frequency, and RSEL configuration data.

## Key Architecture Components

### Main Application (mpw2.py)
- **GasAnalyzer**: Main Qt window with multi-axis plotting and real-time monitoring
- **DataContainer**: Centralized storage for sensor measurements (timestamps, capacitance, temperature, humidity, RSEL data, oscillator data)
- **TimeAxisItem**: Custom PyQtGraph axis for time formatting (HH:MM:SS)
- **CustomViewBox**: Restricted zoom behavior (X-axis only, with MAX_X_RANGE limit of 3600 seconds)
- **ErrorDialog**: Enhanced error display with copyable text

### Modular Components (modules/)
- **serial_manager.py**: Core serial communication (SerialManager, DualSerialManager, SerialConfig, SerialPortScanner)
- **serial_config_gui.py**: Serial port configuration GUI
- **rtt_module.py**: RTT (Real Time Transfer) via pylink for J-Link debugging
- **rtt_gui.py**: RTT connection GUI
- **ppk2_module.py**: Nordic PPK2 power profiler integration
- **A344xxx.py**: VISA instrument control (Keysight A344xxx DMM)
- **theme_manager.py**: Application theme management

### Data Processing
- **Multi-format parsing**: Raw log files (.txt), CSV exports (.csv), Excel files (.xlsx)
- **Multi-encoding support**: UTF-8, CP949, EUC-KR, Latin-1 (handles Korean text)
- **Real-time monitoring**: QTimer-based log file monitoring with incremental parsing
- **SHT41 data correlation**: Groups multiple sensor readings and calculates averages
- **Automatic CSV export**: Generates structured CSV files alongside log analysis (controlled by CSV_AUTO_CONVERT flag)

### Visualization Architecture
- **Multi-axis plotting**: Each data type uses independent ViewBox with its own Y-axis
  - C avg/delta (capacitance average and sigma)
  - Temperature and Humidity (from SHT41 sensor)
  - RSEL data (RSEL16_R, RADD64_M, C_DELAY_M, C)
  - OSC data (oscillator frequency, average, delta)
- **Interactive legends**: Click to toggle plot visibility, with DEFAULT_PLOT_VISIBILITY settings
- **Analysis lines**: Movable vertical lines (A & B) with real-time statistics calculation
- **ViewBox synchronization**: `update_viewbox_geometries()` maintains geometry across multiple ViewBoxes
- **Statistics panel**: Tabbed interface showing avg/std/min/max for data ranges between analysis lines

## Commands

### Building the Application
```bash
# Build standalone executable with PyInstaller
rebuild.cmd
```
This script:
1. Cleans dist/, build/, and __pycache__ directories
2. Runs PyInstaller with mpw2.spec configuration
3. Creates mpw2.zip archive of the distribution
4. Generates python_modules.txt with dependency list

### Development Workflow
```bash
# Run the application directly
python mpw2.py

# Generate Python module list (dependencies snapshot)
make_module_list.cmd
```

## Data Format Support

### Log File Patterns (Regex-based parsing)
- **Timestamp**: `[ 2025/09/26 12:30:51.421 ]`
- **C avg/sigma**: `C avg: 829.819320 ± 0.899683 fF`
- **SHT41 individual**: `SHT41 (1) = 26.35 ℃, Humidity = 51.16 %`
- **SHT41 average**: `3 Times Average = 26.74 ℃, Sigma = 0.05`
- **RSEL data**: `RSEL16_R: 123, RADD64_M: 456, C_DELAY_M: 7.89 C= 12.34 fF`
- **OSC frequency**: `counts. 1.234 GHz`
- **OSC average**: `Average : 1.234 ± 0.005 GHz`

### CSV/Excel Export Format
Columns: Time, C_Avg, C_Sigma, Temperature, Humidity, RSEL16_R, RADD64_M, C_DELAY_M, C, OSC, OSC_Avg, OSC_Delta

## Development Guidelines

### Code Structure
- **UI setup**: Centralized in `setup_ui()` (menu, toolbar, statistics panel)
- **Graph setup**: `setup_graph()` creates multi-axis plotting infrastructure
- **Connections**: `setup_connections()` links signals for real-time monitoring
- **Parsing logic**: Separated by format (`parse_log_file()`, `parse_csv_file()`, `parse_excel_file()`)
- **Statistics**: `calculate_stats()` computes metrics for data between analysis lines
- **ViewBox sync**: `update_viewbox_geometries()` maintains alignment across multiple Y-axes

### Key Implementation Details
- **Multiple ViewBoxes**: Each data type (temp, humidity, C sigma, RSEL, OSC) has its own ViewBox for independent Y-axis scaling
- **Legend interaction**: Custom mouse event handling (`mousePressEvent`) toggles plot visibility
- **Analysis lines**: InfiniteLine objects with `sigPositionChanged` callbacks for real-time statistics
- **Memory management**: DataContainer is recreated on file load to prevent stale data
- **Range synchronization**: `_updating_ranges` flag prevents recursive updates when syncing ViewBox ranges
- **Real-time monitoring**: `log_monitor_timer` polls file changes and calls `parse_new_log_data()` for incremental updates

### Testing Considerations
- Test with various log file encodings (especially Korean text in SHT41 lines)
- Verify CSV/Excel backward compatibility when adding new data fields
- Test analysis line positioning with different data ranges (empty ranges, single points)
- Validate statistics calculations with edge cases
- Check ViewBox geometry synchronization when resizing window
- Test legend toggling with missing data types (e.g., logs without C avg, RSEL, or OSC data)
- Verify DEFAULT_PLOT_VISIBILITY settings apply correctly on file open

### Known Issues to Address
1. **Missing data legend bug**: When C Avg data is absent, legend item doesn't appear
2. **Empty plot behavior**: Graphs without data behave differently from graphs with data (inconsistent interaction)

## File Structure
- `mpw2.py`: Main application (GasAnalyzer with multi-axis plotting)
- `mpw2.spec`: PyInstaller build configuration
- `rebuild.cmd`: Build automation script
- `make_module_list.cmd`: Dependency snapshot generator
- `test.py`: Dual-axis plotting example/reference code
- `SJIT_icon.ico`: Application icon
- `modules/`: Modular components (serial, RTT, PPK2, DMM, theme)
- `logs/`: Runtime log storage directory
- `dist/`: Build output directory (gitignored)
- `python_modules.txt`: Auto-generated dependency list
