import pandas as pd
from fastapi import HTTPException
from pandas.errors import EmptyDataError, ParserError


def read_csv_file(file_path: str) -> pd.DataFrame:
    try:
        return pd.read_csv(file_path)
    except UnicodeDecodeError:
        try:
            return pd.read_csv(file_path, encoding="utf-8-sig")
        except UnicodeDecodeError:
            return pd.read_csv(file_path, encoding="latin1")
    except EmptyDataError as exc:
        raise HTTPException(
            status_code=400,
            detail="CSV file is empty or has no readable columns.",
        ) from exc
    except ParserError as exc:
        raise HTTPException(
            status_code=400,
            detail=(
                "Invalid CSV format. One or more rows have a different number "
                "of fields than the header. Check commas inside text values, "
                "missing quotes, or the delimiter. Original parser error: "
                f"{exc}"
            ),
        ) from exc
