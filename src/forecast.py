"""Small baseline benchmark on pre-promotion revenue only; not a demand model."""
import numpy as np
import pandas as pd


def benchmark(sales, target, holdout=4):
    weekly = sales[(sales.period=='Pre') & (sales.category_name==target)].groupby('week_start_date').revenue.sum().sort_index()
    if len(weekly) <= holdout+2:
        raise ValueError('Insufficient pre-promotion history for forecasting')
    train, actual = weekly.iloc[:-holdout], weekly.iloc[-holdout:]
    h=np.arange(1,holdout+1)
    predictions={'Last week':np.repeat(train.iloc[-1],holdout),
                 'Four-week mean':np.repeat(train.iloc[-4:].mean(),holdout),
                 'Drift':np.maximum(0,train.iloc[-1]+h*(train.iloc[-1]-train.iloc[0])/(len(train)-1))}
    rows=[]
    for name,pred in predictions.items():
        for date,y,yhat in zip(actual.index,actual,pred):
            rows.append({'model':name,'week_start_date':date.strftime('%Y-%m-%d'),'actual_revenue':y,'predicted_revenue':yhat,
                         'train_end':train.index.max().strftime('%Y-%m-%d')})
    detail=pd.DataFrame(rows)
    metrics=[]
    for name,g in detail.groupby('model'):
        metrics.append({'model':name,'mae_usd':float(abs(g.actual_revenue-g.predicted_revenue).mean()),
                        'wape':float(abs(g.actual_revenue-g.predicted_revenue).sum()/g.actual_revenue.abs().sum()),
                        'train_weeks':len(train),'holdout_weeks':holdout})
    return detail,pd.DataFrame(metrics)
