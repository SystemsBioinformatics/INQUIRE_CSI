"""Small helpers shared by the cleanup notebooks."""

from datetime import datetime

import pandas as pd


def ts():
    """Current time as 'YYYY-MM-DD HH:MM:SS' for progress messages."""
    return datetime.now().strftime("%Y-%m-%d %H:%M:%S")


def print_overwrite(msg, width=120):
    """Print a message that overwrites the previous progress message."""
    print(" " * width, end="\r")  # clear line
    print(msg, end="\r", flush=True)


def df_stats(df, df_name, sort_by_unique=True, show=True):
    """Print the shape and show per-column dtype, unique and missing counts.

    Returns the per-column stats DataFrame. With ``sort_by_unique`` the table
    is sorted by descending number of unique values.
    """
    stats = pd.DataFrame(
        {
            "column": df.columns,
            "dtype": [df[c].dtype for c in df.columns],
            "n_unique": [df[c].nunique(dropna=True) for c in df.columns],
            "n_missing": [df[c].isna().sum() for c in df.columns],
            "pct_missing": [round(df[c].isna().mean() * 100, 2) for c in df.columns],
        }
    )
    if sort_by_unique:
        stats = stats.sort_values(by="n_unique", ascending=False)

    print(f"\n{'=' * 80}")
    print(df_name)
    print("=" * 80)
    print(f"Rows: {len(df):,}")
    print(f"Columns: {len(df.columns):,}")

    if show:
        try:
            from IPython.display import display

            display(stats)
        except ImportError:
            print(stats.to_string(index=False))
    return stats
