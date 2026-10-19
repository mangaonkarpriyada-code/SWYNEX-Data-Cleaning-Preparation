
from pathlib import Path
import pandas as pd
import numpy as np

# ----------------------------------
# 1. Define project file locations
# ----------------------------------
BASE_DIR = Path(__file__).resolve().parent
DATA_DIR = BASE_DIR / "data"

INPUT_FILE = DATA_DIR / "raw_student_data.csv"
OUTPUT_FILE = BASE_DIR / "cleaned_student_data.csv"
REPORT_FILE = BASE_DIR / "cleaning_report.txt"

# ----------------------------------
# 2. Load the raw dataset
# ----------------------------------
if not INPUT_FILE.exists():
    raise FileNotFoundError(
        "Dataset not found: {INPUT_FILE}\n"
        "Check that raw_student_data.csv is inside the data folder."
    )

df = pd.read_csv(INPUT_FILE)

print("=" * 55)
print("SWYNEX - STUDENT DATA CLEANING AND PREPARATION")
print("=" * 55)

original_rows, original_columns = df.shape

print("\nOriginal dataset shape:", df.shape)
print("\nFirst five rows:")
print(df.head().to_string())

# ----------------------------------
# 3. Inspect data quality
# ----------------------------------
print("\nOriginal column names:")
print(df.columns.tolist())

print("\nOriginal data types:")
print(df.dtypes.to_string())

print("\nMissing values by column:")
print(df.isnull().sum().to_string())

print("\nExact duplicate rows:", df.duplicated().sum())

initial_missing = int(df.isnull().sum().sum())
initial_duplicates = int(df.duplicated().sum())

# ----------------------------------
# 4. Standardize column names
# ----------------------------------
df.columns = (
    df.columns.astype(str)
    .str.strip()
    .str.lower()
    .str.replace(r"[^a-z0-9]+", "_", regex=True)
    .str.strip("_")
)

# ----------------------------------
# 5. Standardize text fields
# ----------------------------------
text_columns = df.select_dtypes(
    include=["object", "string"]
).columns.tolist()

for column in text_columns:
    df[column] = df[column].map(
        lambda value: value.strip()
        if isinstance(value, str) else value
    )

    df[column] = df[column].replace(
        r"^\s*$", np.nan, regex=True
    )

# Standardize capitalization for common categories
for column in ["gender", "department", "grade"]:
    if column in df.columns:
        df[column] = df[column].str.title()

# ----------------------------------
# 6. Convert numeric columns
# ----------------------------------
numeric_candidates = [
    "age",
    "attendance_percentage",
    "internal_marks",
    "final_marks"
]

for column in numeric_candidates:
    if column in df.columns:
        df[column] = pd.to_numeric(
            df[column], errors="coerce"
        )

# ----------------------------------
# 7. Handle invalid numeric values
# ----------------------------------
range_rules = {
    "age": (5, 100),
    "attendance_percentage": (0, 100),
    "internal_marks": (0, 100),
    "final_marks": (0, 100)
}

invalid_counts = {}

for column, (minimum, maximum) in range_rules.items():
    if column in df.columns:
        invalid = (
            df[column].notna()
            & ~df[column].between(minimum, maximum)
        )

        invalid_counts[column] = int(invalid.sum())

        # Invalid values become missing values.
        df.loc[invalid, column] = np.nan

# ----------------------------------
# 8. Remove exact duplicate rows
# ----------------------------------
df = df.drop_duplicates().copy()

# ----------------------------------
# 9. Fill missing values
# ----------------------------------
numeric_columns = df.select_dtypes(
    include="number"
).columns.tolist()

for column in numeric_columns:
    if df[column].isnull().any():
        median_value = df[column].median()

        if pd.notna(median_value):
            df[column] = df[column].fillna(median_value)

text_columns = df.select_dtypes(
    include=["object", "string"]
).columns.tolist()

for column in text_columns:
    if df[column].isnull().any():
        mode_values = df[column].mode(dropna=True)

        if not mode_values.empty:
            fill_value = mode_values.iloc[0]
        else:
            fill_value = "Unknown"

        df[column] = df[column].fillna(fill_value)

# ----------------------------------
# 10. Validate the cleaned dataset
# ----------------------------------
final_missing = int(df.isnull().sum().sum())
final_duplicates = int(df.duplicated().sum())

print("\nFinal dataset shape:", df.shape)
print("Missing cells remaining:", final_missing)
print("Duplicate rows remaining:", final_duplicates)

print("\nMissing values after cleaning:")
print(df.isnull().sum().to_string())

# ----------------------------------
# 11. Save the cleaned dataset
# ----------------------------------
df.to_csv(OUTPUT_FILE, index=False)

# ----------------------------------
# 12. Create a cleaning report
# ----------------------------------
report_lines = [
    "SWYNEX DATA CLEANING REPORT",
    "=" * 35,
    f"Original rows: {original_rows}",
    f"Original columns: {original_columns}",
    f"Final rows: {len(df)}",
    f"Final columns: {len(df.columns)}",
    f"Missing cells initially: {initial_missing}",
    f"Duplicate rows initially: {initial_duplicates}",
    f"Duplicate rows removed: {initial_duplicates}",
    f"Missing cells remaining: {final_missing}",
    f"Duplicate rows remaining: {final_duplicates}",
    "",
    "Invalid values detected by field:",
]

for column, count in invalid_counts.items():
    report_lines.append(f"{column}: {count}")

report_lines.extend([
    "",
    "Final data types:",
    df.dtypes.to_string()
])

REPORT_FILE.write_text(
    "\n".join(report_lines),
    encoding="utf-8"
)

print("\nFiles created successfully:")
print(OUTPUT_FILE)
print(REPORT_FILE)
print("\nCleaning process completed.")
