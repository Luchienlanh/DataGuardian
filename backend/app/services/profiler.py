from app.services.csv_reader import read_csv_file

def profile_csv(file_path):
    df = read_csv_file(file_path)
    
    return {
        'num_rows': len(df),
        'num_columns': len(df.columns),
        'columns_details': [
            {
                'name': col,
                'dtype': str(df[col].dtype),
                'null_count': int(df[col].isnull().sum()),
                'unique_count': int(df[col].nunique(dropna=True)),
                'null_ratio': float(df[col].isna().mean()),
                'duplicate_count': int(df[col].duplicated().sum()),
            }
            for col in df.columns
        ],
    }
