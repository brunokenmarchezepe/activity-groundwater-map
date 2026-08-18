from pathlib import Path
from typing import Optional
import zipfile
import xml.etree.ElementTree as ET
import sys
import argparse

import pandas as pd

START_DATE = pd.Timestamp("2024-10-01")
END_DATE = pd.Timestamp("2025-09-30 23:59:59")

# Default paths (for backward compatibility)
DEFAULT_BASIN_DIR = Path("/Volumes/Marchezepe/GitHub/activity-groundwater-map/north_carolina_wells")

GROUND_SURFACE_PARAMETER = "Water depth [from the ground surface]"
TOP_OF_WELL_PARAMETER = "Water depth [from the top of the well]"
WATER_LEVEL_ELEVATION_PARAMETER = "Water level elevation a.m.s.l."
DESCRIPTION_ROW_ID = "As recorded in the original database."

NS = {
    "office": "urn:oasis:names:tc:opendocument:xmlns:office:1.0",
    "table": "urn:oasis:names:tc:opendocument:xmlns:table:1.0",
    "text": "urn:oasis:names:tc:opendocument:xmlns:text:1.0",
}

TABLE_TAG = f"{{{NS['table']}}}table"
ROW_TAG = f"{{{NS['table']}}}table-row"
CELL_TAG = f"{{{NS['table']}}}table-cell"
COVERED_CELL_TAG = f"{{{NS['table']}}}covered-table-cell"
PARAGRAPH_TAG = f"{{{NS['text']}}}p"
TABLE_NAME_ATTR = f"{{{NS['table']}}}name"
COLUMN_REPEAT_ATTR = f"{{{NS['table']}}}number-columns-repeated"
ROW_REPEAT_ATTR = f"{{{NS['table']}}}number-rows-repeated"
VALUE_ATTR = f"{{{NS['office']}}}value"
DATE_VALUE_ATTR = f"{{{NS['office']}}}date-value"
STRING_VALUE_ATTR = f"{{{NS['office']}}}string-value"


def extract_cell_value(cell: ET.Element) -> str:
    paragraphs = []
    for paragraph in cell.iter(PARAGRAPH_TAG):
        text_value = "".join(paragraph.itertext()).strip()
        if text_value:
            paragraphs.append(text_value)

    if paragraphs:
        return "\n".join(paragraphs)

    for attr_name in (VALUE_ATTR, DATE_VALUE_ATTR, STRING_VALUE_ATTR):
        if attr_name in cell.attrib:
            return cell.attrib[attr_name].strip()

    return ""


def read_ods_sheet(file_path: Path, sheet_name: str) -> pd.DataFrame:
    with zipfile.ZipFile(file_path) as ods_file:
        with ods_file.open("content.xml") as content_xml:
            root = ET.parse(content_xml).getroot()

    for table in root.iter(TABLE_TAG):
        if table.attrib.get(TABLE_NAME_ATTR) != sheet_name:
            continue

        rows = []
        for row in table.findall(ROW_TAG):
            row_values = []
            for cell in row:
                if cell.tag not in {CELL_TAG, COVERED_CELL_TAG}:
                    continue

                value = extract_cell_value(cell)
                repeat = int(cell.attrib.get(COLUMN_REPEAT_ATTR, "1"))
                row_values.extend([value] * repeat)

            while row_values and row_values[-1] == "":
                row_values.pop()

            if not row_values:
                continue

            repeat_rows = int(row.attrib.get(ROW_REPEAT_ATTR, "1"))
            for _ in range(repeat_rows):
                rows.append(row_values.copy())

        if not rows:
            return pd.DataFrame()

        header = normalize_headers(rows[0])
        width = len(header)
        data_rows = []
        for row_values in rows[1:]:
            if not any(value != "" for value in row_values):
                continue
            padded_row = row_values[:width] + [""] * max(width - len(row_values), 0)
            data_rows.append(padded_row)

        return pd.DataFrame(data_rows, columns=header)

    raise ValueError(f"Sheet '{sheet_name}' not found in {file_path}")


def normalize_headers(headers: list[str]) -> list[str]:
    normalized = []
    duplicates: dict[str, int] = {}

    for index, header in enumerate(headers):
        column_name = str(header).strip()
        if not column_name:
            column_name = f"Unnamed: {index}"

        duplicate_count = duplicates.get(column_name, 0)
        if duplicate_count:
            column_name = f"{column_name}.{duplicate_count}"
        duplicates[str(header).strip() or f"Unnamed: {index}"] = duplicate_count + 1
        normalized.append(column_name)

    return normalized


def to_numeric_series(values: pd.Series) -> pd.Series:
    normalized = values.astype("string").str.strip().str.replace(",", ".", regex=False)
    return pd.to_numeric(normalized, errors="coerce")


def convert_length_to_meters(values: pd.Series, units: pd.Series) -> pd.Series:
    converted = to_numeric_series(values)
    normalized_units = units.astype("string").str.strip().str.lower()

    converted.loc[normalized_units == "ft"] *= 0.3048
    converted.loc[~normalized_units.isin(["m", "ft"])] = pd.NA

    return converted


def load_wells_metadata(basin_dir: Path) -> pd.DataFrame:
    wells_file = basin_dir / "wells.ods"
    wells_df = read_ods_sheet(wells_file, "General Information")
    wells_df = wells_df.loc[wells_df["ID"] != DESCRIPTION_ROW_ID].copy()

    wells_df["ID"] = wells_df["ID"].astype("string").str.strip()
    wells_df["lat"] = to_numeric_series(wells_df["Latitude"])
    wells_df["long"] = to_numeric_series(wells_df["Longitude"])
    wells_df["altitude"] = convert_length_to_meters(
        wells_df["Ground surface elevation"],
        wells_df["Unnamed: 10"],
    )
    wells_df["top_of_well_elevation_m"] = convert_length_to_meters(
        wells_df["Top of well elevation"],
        wells_df["Unnamed: 14"],
    )

    return wells_df[["ID", "lat", "long", "altitude", "top_of_well_elevation_m"]]


def calculate_well_median(file_path: Path, metadata: pd.Series) -> Optional[float]:
    level_df = read_ods_sheet(file_path, "Groundwater Level")
    level_df = level_df.loc[level_df["ID"] != DESCRIPTION_ROW_ID].copy()

    if level_df.empty:
        return None

    level_df["Date and Time"] = pd.to_datetime(
        level_df["Date and Time"],
        format="mixed",
        errors="coerce",
    )
    level_df["value_m"] = convert_length_to_meters(level_df["Value"], level_df["Unit"])
    level_df = level_df.loc[
        level_df["Date and Time"].between(START_DATE, END_DATE)
        & level_df["value_m"].notna()
    ].copy()

    if level_df.empty:
        return None

    level_df["water_depth_m"] = pd.NA
    ground_surface_mask = level_df["Parameter"] == GROUND_SURFACE_PARAMETER
    level_df.loc[ground_surface_mask, "water_depth_m"] = level_df.loc[
        ground_surface_mask,
        "value_m",
    ]

    if pd.notna(metadata["altitude"]) and pd.notna(metadata["top_of_well_elevation_m"]):
        top_of_well_offset = metadata["top_of_well_elevation_m"] - metadata["altitude"]
        top_of_well_mask = level_df["Parameter"] == TOP_OF_WELL_PARAMETER
        level_df.loc[top_of_well_mask, "water_depth_m"] = (
            level_df.loc[top_of_well_mask, "value_m"] + top_of_well_offset
        )

    if pd.notna(metadata["altitude"]):
        elevation_mask = level_df["Parameter"] == WATER_LEVEL_ELEVATION_PARAMETER
        level_df.loc[elevation_mask, "water_depth_m"] = (
            metadata["altitude"] - level_df.loc[elevation_mask, "value_m"]
        )

    level_df["water_depth_m"] = pd.to_numeric(level_df["water_depth_m"], errors="coerce")
    level_df = level_df.loc[level_df["water_depth_m"].notna()]

    if level_df.empty:
        return None

    return float(level_df["water_depth_m"].median())


def calculate_median_water_depth(basin_dir: Path) -> None:
    monitoring_dir = basin_dir / "monitoring"
    
    if not monitoring_dir.exists():
        print(f"Error: Monitoring directory not found at {monitoring_dir}")
        return
    
    wells_metadata = load_wells_metadata(basin_dir)
    metadata_by_id = wells_metadata.set_index("ID")
    median_depths = []

    for file_path in sorted(monitoring_dir.glob("*.ods")):
        well_id = file_path.stem
        if well_id not in metadata_by_id.index:
            continue

        median_depth = calculate_well_median(file_path, metadata_by_id.loc[well_id])
        if median_depth is None:
            continue

        median_depths.append(
            {
                "ID": well_id,
                "median_water_depth": median_depth,
            }
        )

    median_depths_df = pd.DataFrame(median_depths)
    final_df = wells_metadata.merge(median_depths_df, on="ID", how="left")
    final_df = final_df[["ID", "lat", "long", "altitude", "median_water_depth"]]
    
    # Create output filename based on basin directory name
    basin_name = basin_dir.name
    output_csv = basin_dir / f"{basin_name}_median_water_depth_2024-10-01_to_2025-09-30.csv"
    final_df.to_csv(output_csv, index=False)

    print(f"Output saved to {output_csv}")
    print(f"Rows written: {len(final_df)}")
    print(f"Wells with median water depth: {final_df['median_water_depth'].notna().sum()}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Process groundwater wells data and calculate median water depth."
    )
    parser.add_argument(
        "--basin-dir",
        type=Path,
        default=DEFAULT_BASIN_DIR,
        help=f"Path to the basin directory (default: {DEFAULT_BASIN_DIR})",
    )
    
    args = parser.parse_args()
    basin_dir = args.basin_dir.resolve()
    
    if not basin_dir.exists():
        print(f"Error: Basin directory not found at {basin_dir}")
        sys.exit(1)
    
    if not (basin_dir / "wells.ods").exists():
        print(f"Error: wells.ods not found in {basin_dir}")
        sys.exit(1)
    
    print(f"Processing basin: {basin_dir.name}")
    calculate_median_water_depth(basin_dir)
