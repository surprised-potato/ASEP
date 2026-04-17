import pandas as pd
db = pd.read_excel('aisc-shapes-database-v160-2.xlsx', sheet_name='Database v16.0')
cols = ['Type', 'AISC_Manual_Label', 'd', 'bf', 'b', 'tw', 'tf', 't']
print(db[db['Type'] == 'WT'][cols].head(1))
print(db[db['Type'] == 'L'][cols].head(1))
print(db[db['Type'] == '2L'][cols].head(1))
