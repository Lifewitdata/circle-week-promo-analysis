"""Fail closed on incompatible inputs; report all contract failures."""
import pandas as pd
import numpy as np

SALES_COLUMNS = ['store_id', 'region', 'test_group', 'category_id', 'category_name',
                 'week_start_date', 'period', 'revenue', 'units_sold']


def validate(sales, stores, products, promotions):
    errors = []
    required = [(sales, SALES_COLUMNS, 'sales'),
                (stores, ['store_id', 'region', 'test_group', 'store_format', 'sq_footage'], 'stores'),
                (products, ['category_id', 'category_name'], 'products'),
                (promotions, ['promo_id', 'category_targeted', 'promo_start_date', 'promo_end_date'], 'promotions')]
    for df, columns, name in required:
        if not set(columns) <= set(df.columns):
            errors.append(f'{name}: missing required columns')
        elif df.empty or df[columns].isna().any().any():
            errors.append(f'{name}: empty table or missing required values')
    if errors:
        raise ValueError('; '.join(errors))
    s = sales.copy()
    for df, key, name in [(stores, 'store_id', 'stores'), (products, 'category_id', 'products'), (promotions, 'promo_id', 'promotions')]:
        if df[key].duplicated().any():
            errors.append(f'{name}: duplicate primary key')
    if s.duplicated(['store_id', 'category_id', 'week_start_date']).any():
        errors.append('sales: duplicate store/category/week key')
    dates = pd.to_datetime(s.week_start_date, errors='coerce')
    if dates.isna().any() or (dates.dt.dayofweek != 0).any():
        errors.append('sales: dates must be valid Monday week starts')
    s['week_start_date'] = dates
    for col in ['revenue', 'units_sold']:
        v = pd.to_numeric(s[col], errors='coerce')
        if not np.isfinite(v).all() or (v < 0).any():
            errors.append(f'sales: {col} must be finite and nonnegative')
        if col == 'units_sold' and (v % 1 != 0).any():
            errors.append('sales: units_sold must be whole units')
        s[col] = v
    if (s.units_sold == 0).any() and (s.loc[s.units_sold == 0, 'revenue'] != 0).any():
        errors.append('sales: positive revenue with zero units')
    if set(s.test_group) != {'Test', 'Control'} or set(s.period) != {'Pre', 'Post'}:
        errors.append('sales: both assignment groups and both periods required')
    if not set(s.store_id) <= set(stores.store_id) or not set(s.category_id) <= set(products.category_id):
        errors.append('sales: unknown dimension key')
    if not stores.store_id.is_unique or not products.category_id.is_unique:
        raise ValueError('; '.join(errors))
    joined = s.merge(stores[['store_id', 'region', 'test_group']], on='store_id', how='left', suffixes=('', '_dim'), validate='many_to_one')
    if ((joined.region != joined.region_dim) | (joined.test_group != joined.test_group_dim)).any():
        errors.append('sales: assignment/region does not match stores')
    cat = s.merge(products[['category_id', 'category_name']], on='category_id', how='left', suffixes=('', '_dim'), validate='many_to_one')
    if (cat.category_name != cat.category_name_dim).any():
        errors.append('sales: category name does not match products')
    if len(promotions) != 1:
        errors.append('exactly one promotion is supported')
    else:
        start = pd.to_datetime(promotions.iloc[0].promo_start_date, errors='coerce')
        end = pd.to_datetime(promotions.iloc[0].promo_end_date, errors='coerce')
        if pd.isna(start) or pd.isna(end) or start > end:
            errors.append('promotion dates are invalid')
        elif ((s.period == 'Pre') != (dates < start)).any() or (dates > end).any():
            errors.append('sales: period does not match promotion dates')
        if promotions.iloc[0].category_targeted not in set(products.category_name):
            errors.append('promotion has unknown target category')
    weeks = sorted(dates.dropna().unique())
    if len(weeks) < 8 or (pd.Series(weeks).diff().dropna() != pd.Timedelta(days=7)).any():
        errors.append('sales: insufficient or nonconsecutive weekly history')
    expected = len(stores) * len(products) * len(weeks)
    if len(s) != expected:
        errors.append('sales: incomplete store/category/week panel')
    if s.groupby('period').week_start_date.nunique().nunique() != 1:
        errors.append('equal pre and post windows required')
    if stores.groupby('test_group').size().min() < 2:
        errors.append('at least two stores per assignment required')
    if errors:
        raise ValueError('; '.join(errors))
    return s, {'status': 'passed', 'rows': len(s), 'stores': len(stores),
               'categories': len(products), 'weeks': len(weeks),
               'duplicate_keys': 0, 'missing_required_values': 0,
               'complete_panel': True}
