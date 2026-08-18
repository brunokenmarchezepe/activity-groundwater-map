# Groundwater Wells Data Processing

A Python program that analyzes groundwater monitoring data from wells and calculates median water depth statistics.

## What Does This Do?

This program reads monitoring data from `.ods` (spreadsheet) files and:
- Extracts well information (location, elevation)
- Processes water depth measurements over time
- Calculates the median water depth for each well
- Generates a CSV file with results

Perfect for environmental science, hydrology, or GIS studies.

---

## Getting Started (No Coding Experience Needed!)

### Step 1: Install Python

If you don't have Python installed:

1. Go to [python.org](https://www.python.org/downloads/)
2. Download Python 3.9 or newer
3. Run the installer and **check the box that says "Add Python to PATH"**
4. Click Install

**To verify Python is installed:**
- Open Terminal (Mac) or Command Prompt (Windows)
- Type: `python --version`
- You should see something like `Python 3.11.0`

### Step 2: Set Up the Project

1. **Download or clone this project** to your computer
2. **Open Terminal** (Mac) or **PowerShell** (Windows)
3. **Navigate to the project folder:**
   ```bash
   cd /path/to/activity-groundwater-map
   ```
   *(Replace `/path/to/` with your actual folder location)*

### Step 3: Create a Virtual Environment (Recommended)

This keeps dependencies isolated for this project.

```bash
python -m venv .venv
```

**Activate the virtual environment:**
- **Mac/Linux:**
  ```bash
  source .venv/bin/activate
  ```
- **Windows:**
  ```bash
  .venv\Scripts\activate
  ```

You should see `(.venv)` appear at the start of your terminal line.

### Step 4: Install Required Libraries

```bash
pip install pandas
```

This installs the "pandas" library needed to process data.

---

## How to Run the Program

### Option 1: Process North Carolina Wells (Default)

```bash
python process_wells.py
```

This will read from the `north_carolina_wells/` folder and create an output file.

### Option 2: Process Catawba Basin Wells

```bash
python process_wells.py --basin-dir ./catawba_basin_wells
```

This will read from the `catawba_basin_wells/` folder instead.

### Option 3: Process Any Basin Folder

```bash
python process_wells.py --basin-dir /path/to/your/basin/folder
```

Replace `/path/to/your/basin/folder` with the actual path to your data folder.

---

## What You Need in Your Basin Folder

For the program to work, your basin folder must contain:

```
your_basin_folder/
├── wells.ods              (spreadsheet with well information)
└── monitoring/            (folder with monitoring data)
    ├── well_1.ods
    ├── well_2.ods
    └── ...
```

**Files needed:**
- **wells.ods** — Main spreadsheet with well metadata (ID, latitude, longitude, elevation)
- **monitoring/** folder — Contains individual .ods files, one per well, with water level measurements

The spreadsheet files must have these sheets:
- "General Information" (in wells.ods) — Contains well metadata
- "Groundwater Level" (in each monitoring file) — Contains water depth measurements

---

## Understanding the Output

When you run the program, it creates a CSV file with results:

**Example output filename:**
```
north_carolina_wells_median_water_depth_2024-10-01_to_2025-09-30.csv
```

**What's in the file:**
| ID | lat | long | altitude | median_water_depth |
|---|---|---|---|---|
| W001 | 35.234 | -80.123 | 245.5 | 8.2 |
| W002 | 35.245 | -80.145 | 250.1 | 12.5 |

**Columns explained:**
- **ID** — Well identifier
- **lat** — Latitude coordinate
- **long** — Longitude coordinate  
- **altitude** — Ground elevation in meters
- **median_water_depth** — Average water depth in meters (main result)

Open the CSV file in Excel, Google Sheets, or any spreadsheet program to view results.

---

## Common Commands Reference

| Task | Command |
|------|---------|
| Activate virtual environment | `source .venv/bin/activate` (Mac) or `.venv\Scripts\activate` (Windows) |
| Deactivate virtual environment | `deactivate` |
| Run program (North Carolina) | `python process_wells.py` |
| Run program (Catawba Basin) | `python process_wells.py --basin-dir ./catawba_basin_wells` |
| Check Python version | `python --version` |
| List installed packages | `pip list` |

---

## Troubleshooting

### Error: "Python is not recognized"
- **Solution:** Python isn't in your PATH. Reinstall Python and check "Add Python to PATH"

### Error: "No such file or directory"
- **Solution:** You're in the wrong folder. Use `cd` to navigate to the project folder first
- Example: `cd ~/Documents/activity-groundwater-map`

### Error: "ModuleNotFoundError: No module named 'pandas'"
- **Solution:** Install pandas:
  ```bash
  pip install pandas
  ```

### Error: "wells.ods not found"
- **Solution:** The basin folder doesn't have a `wells.ods` file. Check your folder structure matches the requirements above.

### Error: "Monitoring directory not found"
- **Solution:** Create a `monitoring/` folder inside your basin directory

### No output file created
- **Solution:** Check the terminal for error messages. Make sure:
  - The `wells.ods` file exists
  - The `monitoring/` folder exists and has .ods files
  - The date range (Oct 1, 2024 - Sept 30, 2025) matches your data

---

## For Course Instructors

This script is ideal for teaching:
- **Data Processing** — Reading and parsing structured data
- **Scientific Computing** — Unit conversions, statistical analysis
- **Environmental Science** — Real groundwater monitoring workflows
- **Practical Python** — Type hints, error handling, CLI arguments

**Suggestions for students:**
1. Modify the date range to filter different time periods
2. Add visualization (matplotlib) to plot water depth trends
3. Add more statistics (mean, std deviation, quantiles)
4. Extend to compare multiple basins
5. Write unit tests for the helper functions

---

## Need Help?

**Check the following:**
1. Are you in the project folder? (`cd` to the right location)
2. Is Python installed? (`python --version`)
3. Is pandas installed? (`pip install pandas`)
4. Do you have the required data files? (wells.ods + monitoring folder)

For more advanced questions, consult the code comments or contact your instructor.

---

## Project Structure

```
activity-groundwater-map/
├── README.md                      (this file)
├── process_wells.py               (main program)
├── north_carolina_wells/          (example data)
│   ├── wells.ods
│   ├── monitoring/
│   └── *.csv (output files)
├── catawba_basin_wells/           (example data)
│   ├── wells.ods
│   ├── monitoring/
│   └── *.csv (output files)
└── .venv/                         (virtual environment - created by you)
```

---

## License & Attribution

This project processes environmental monitoring data. All data should be properly attributed to its original sources.
