import pandas as pd
db = pd.read_excel('aisc-shapes-database-v160-2.xlsx', sheet_name='Database v16.0')
print(db[['rx', 'ry', 'rz', 'rx.1', 'ry.1', 'rz.1']].head(10))
