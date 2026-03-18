import pandas as pd
db = pd.read_excel('aisc-shapes-database-v160-2.xlsx', sheet_name='Database v16.0')
l2 = db[db['Type'] == '2L']
l2_zero_spacing = l2[l2['AISC_Manual_Label.1'].str.count('X') == 2]
print(l2_zero_spacing[['AISC_Manual_Label.1', 'A.1', 'W.1', 'rx.1', 'ry.1']].head(10))
