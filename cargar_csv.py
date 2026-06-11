import pandas as pd

df = pd.read_csv('Ies_dept_muni_sex_car_orig.csv',sep=';')
print(df.head())
print('--'*30)
# print(df.info())