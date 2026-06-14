from app.services.csv_reader import read_csv_file

def quality_check(file_path, profile=None, threshold=0.2):
    df = read_csv_file(file_path)
    issues = []

    if profile is None:
        profile = {'num_rows': len(df), 'columns_details': []}

    duplicate_rows = int(df.duplicated().sum())
    if duplicate_rows > 0:
        issues.append({
            'type': 'Duplicate rows',
            'column': None,
            'severity': 'medium',
            'message': f'Found {duplicate_rows} duplicate rows',
            'evidence': {
                'duplicate_count': duplicate_rows,
                'total_count': int(len(df)),
            }
        })
    
    for col in profile['columns_details']:
        if col['null_ratio'] > threshold:
            issues.append({
                'type': 'High null ratio on column',
                'column': col['name'],
                'severity': 'medium',
                'message': f"Column '{col['name']}' has {col['null_ratio']:.1%} null values",
                'evidence': {
                    'null_count': col['null_count'],
                    'total_count': profile['num_rows'],
                    'null_ratio': col['null_ratio'],
                    'threshold': threshold,
                }
            })
    
    for index, col in enumerate(df.columns):
        is_primary_key_candidate = col.lower() == 'id' or (index == 0 and col.lower().endswith('_id'))
        duplicate_count = int(df[col].dropna().duplicated().sum())

        if is_primary_key_candidate and duplicate_count > 0:
            issues.append({
               'type': "Duplicate values in ID column",
               'column': col,
               'severity': 'high',
               'message': f"Column '{col}' contains duplicate values",
               'evidence': {
                   'duplicate_count': duplicate_count,
                   'total_count': int(len(df)),
               }
            })

    for col in df.columns:
        non_null = df[col].dropna()

        if len(non_null) > 0 and int(non_null.nunique()) == 1:
            constant_value = non_null.iloc[0]
            issues.append({
                'type': 'Constant column',
                'column': col,
                'severity': 'low',
                'message': f"Column '{col}' has the same value in every non-null row",
                'evidence': {
                    'unique_count': 1,
                    'constant_value': str(constant_value),
                    'non_null_count': int(len(non_null)),
                    'total_count': int(len(df)),
                }
            })

    return issues
