import pandas as pd
from app.services.csv_reader import read_csv_file


def get_numeric_distribution(df):
    numeric_cols = df.select_dtypes(include='number').columns
    distributions = {}
    
    for col in numeric_cols:
        series = df[col].dropna()
        
        if series.empty:
            continue
        
        counts, bins = pd.cut(series, bins=20, retbins=True)
        hist = counts.value_counts(sort=False)
        
        q1 = float(series.quantile(0.25))
        q3 = float(series.quantile(0.75))
        iqr = q3 - q1
        
        lower_bound = q1 - 1.5 * iqr
        upper_bound = q3 + 1.5 * iqr
        
        outlier_mask = (series < lower_bound) | (series > upper_bound)
        outlier_num = int(outlier_mask.sum())

        distributions[col] = {
            'histogram': {
                'bins': [float(b) for b in bins],
                'counts': [int(c) for c in hist.values],
            },
            'quantiles': {
                'p25': q1,
                'p50': float(series.quantile(0.5)),
                'p75': q3,
                'p95': float(series.quantile(0.95)),
                'p99': float(series.quantile(0.99)),
            },
            'outliers': {
                'method': 'IQR',
                'lower_bound': float(lower_bound),
                'upper_bound': float(upper_bound),
                'num_outliers': outlier_num,
                'rate': float(outlier_num / len(series)) if len(series) > 0 else 0.0,
            }
        }        
    return distributions

def get_categorical_distribution(df):
    categorical_cols = df.select_dtypes(include='object').columns
    distributions = {}
    
    for col in categorical_cols:
        series = df[col].dropna()
        
        if series.empty:
            continue
        
        value_counts = series.value_counts()
        total = int(value_counts.sum())
        
        top_values = [
            {
                'value': str(value),
                'count': int(count),
                'percentage': float(count / total) if total > 0 else 0.0
            }
            for value, count in value_counts.head(10).items()
        ]
        
        rare_values = int((value_counts == 1).sum())
        cardinality_ratio = float(series.nunique() / len(series))
        
        distributions[col] = {
            'top_values': top_values,
            'rare_values': rare_values,
            'cardinality_ratio': cardinality_ratio,
            'unique_values': int(series.nunique()),
        }
    
    return distributions

def get_correlations(df):
    numeric_df = df.select_dtypes(include='number')
    numeric_df = numeric_df.loc[:, numeric_df.nunique(dropna=True) > 1]
    
    if numeric_df.shape[1] < 2:
        return {
            'matrix': {},
            'top_pos': [],
            'top_neg': [],
        }
        
    corr_matrix = numeric_df.corr().fillna(0)
    
    pairs = []
    
    cols = corr_matrix.columns.tolist()
    for i, col_a in enumerate(cols):
        for col_b in cols[i + 1:]:
            value = float(corr_matrix.loc[col_a, col_b])
            pairs.append({
                "columns": [col_a, col_b],
                "correlation": value,
            })
            
    top_pos = sorted(
        [ p for p in pairs if p['correlation'] > 0],
        key=lambda x: x['correlation'],
        reverse=True,
    )[:10]
    
    top_neg = sorted(
        [ p for p in pairs if p['correlation'] < 0],
        key=lambda x: x['correlation'],
    )[:10]
    
    return {
        'matrix': corr_matrix.to_dict(),
        'top_pos': top_pos,
        'top_neg': top_neg,
    }
    

def get_missingness_patterns(df: pd.DataFrame) -> dict:
    missing_df = df.isna()

    row_missing_counts = missing_df.sum(axis=1).value_counts().sort_index()

    row_missing_distribution = [
        {
            "missing_columns": int(missing_count),
            "row_count": int(row_count),
        }
        for missing_count, row_count in row_missing_counts.items()
    ]

    column_pairs = []
    cols = df.columns.tolist()

    for i, col_a in enumerate(cols):
        for col_b in cols[i + 1:]:
            both_missing = int((missing_df[col_a] & missing_df[col_b]).sum())

            if both_missing > 0:
                column_pairs.append({
                    "columns": [col_a, col_b],
                    "both_missing_count": both_missing,
                    "both_missing_rate": float(both_missing / len(df)),
                })

    column_pairs = sorted(
        column_pairs,
        key=lambda x: x["both_missing_count"],
        reverse=True,
    )[:20]

    return {
        "row_missing_distribution": row_missing_distribution,
        "column_pairs": column_pairs,
    }
    
def get_eda_insights(eda: dict) -> list[dict]:
    insights = []

    for col, info in eda["numeric_distributions"].items():
        outlier_rate = info["outliers"]["rate"]

        if outlier_rate > 0.05:
            insights.append({
                "type": "outlier_heavy",
                "column": col,
                "level": "info",
                "message": f"{col} has {outlier_rate:.1%} outliers by IQR.",
            })

    for col, info in eda["categorical_distributions"].items():
        if info["cardinality_ratio"] > 0.8:
            insights.append({
                "type": "high_cardinality",
                "column": col,
                "level": "info",
                "message": f"{col} has high cardinality.",
            })

    return insights

def eda_report(file_path):
    df = read_csv_file(file_path)
    
    eda = {
        'numeric_distributions': get_numeric_distribution(df),
        'categorical_distributions': get_categorical_distribution(df),
        'correlations': get_correlations(df),
        'missingness': get_missingness_patterns(df),
    }
    
    eda['insights'] = get_eda_insights(eda)
    
    return eda
