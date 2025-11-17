from backend.app.model import train_logistic
import pandas as pd
import traceback

if __name__ == '__main__':
    try:
        df = pd.read_csv('..\\data\\ibm_attrition_sample.csv')
        metrics, artifacts = train_logistic(df, target_column='Attrition')
        print('METRICS:', metrics)
        print('ARTIFACTS keys:', list(artifacts.keys()))
    except Exception as e:
        traceback.print_exc()
        print('ERROR:', e)
