import pandas as pd
db = pd.read_excel('aisc-shapes-database-v160-2.xlsx', sheet_name='Database v16.0')
print(db[['AISC_Manual_Label', 'AISC_Manual_Label.1', 'W', 'W.1', 'A', 'A.1']].head(10))
