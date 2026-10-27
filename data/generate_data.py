"""Generate an alternative reproducible fixture; never overwrite committed case data.

The original generator is unavailable. This explicitly creates a NEW simulation,
not a reconstruction of the published 14.89pp result.
"""
import argparse
from pathlib import Path
import numpy as np
import pandas as pd


def generate(output,seed=42,stores_count=60,effect=0.15):
    output=Path(output)
    source=Path(__file__).resolve().parent
    if output.resolve()==source.resolve():
        raise ValueError('Choose a separate output directory to preserve original case data')
    if stores_count<8 or not np.isfinite(effect) or effect < -1:
        raise ValueError('Need at least 8 stores and a finite effect >= -1')
    output.mkdir(parents=True,exist_ok=True)
    if any(output.glob('*.csv')):
        raise ValueError('Output directory already contains CSVs')
    rng=np.random.default_rng(seed)
    products=pd.read_csv(source/'products.csv')
    promotions=pd.read_csv(source/'promotions.csv')
    assignment=np.array(['Test']*(stores_count//2)+['Control']*(stores_count-stores_count//2))
    rng.shuffle(assignment)
    stores=pd.DataFrame({'store_id':[f'S{i:04}' for i in range(stores_count)],
                         'region':rng.choice(['North','South','East','West'],stores_count),
                         'store_format':rng.choice(['Standard','Large','Small'],stores_count),
                         'sq_footage':rng.integers(50000,160000,stores_count),
                         'test_group':assignment})
    rows=[]
    for store in stores.itertuples():
        size=rng.uniform(.8,1.2)
        for category in products.itertuples():
            for week,date in enumerate(pd.date_range('2026-01-05',periods=26,freq='W-MON')):
                post=week>=13
                uplift=effect if post and store.test_group=='Test' and category.category_name=='Electronics' else 0
                units=max(1,round(category.base_weekly_revenue/30*size*(1+.004*week+uplift)*rng.lognormal(0,.06)))
                revenue=round(units*30*rng.uniform(.98,1.02),2)
                rows.append([store.store_id,store.region,store.test_group,category.category_id,category.category_name,date.strftime('%Y-%m-%d'),'Post' if post else 'Pre',revenue,units])
    columns=['store_id','region','test_group','category_id','category_name','week_start_date','period','revenue','units_sold']
    pd.DataFrame(rows,columns=columns).to_csv(output/'sales_weekly.csv',index=False)
    for name,df in [('stores',stores),('products',products),('promotions',promotions)]:
        df.to_csv(output/f'{name}.csv',index=False)
    return pd.DataFrame(rows,columns=columns)


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--output',required=True,type=Path)
    p.add_argument('--seed',type=int,default=42)
    p.add_argument('--stores',type=int,default=60)
    p.add_argument('--effect',type=float,default=.15)
    a=p.parse_args()
    generate(a.output,a.seed,a.stores,a.effect)
