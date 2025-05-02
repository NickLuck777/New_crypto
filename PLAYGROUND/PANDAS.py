import pandas as pd


data = {'frresh_apples': [140, 115, 55], 
        ')oranges': [10, 215, 56], 
        'ban(anas': [130, None, 57]}

df = pd.DataFrame(data, index=['Nick', 'Lars', 'John'])
temp_df = df._append(df)
temp_df.drop_duplicates(inplace=True)

temp_df.rename(columns={'frresh_apples': 'Fresh_apples', ')oranges': 'Frozen_oranges', 'ban(anas': 'Baked_bananas'}, inplace=True)
temp_df.columns = ['Apples', 'Oranges', 'Bananas']
temp_df.columns = [col.upper() for col in temp_df.columns]
# temp_df.dropna(inplace=True)
# temp_df.dropna(axis=1, inplace=True)
ban_col = temp_df['BANANAS']
ban_col.fillna(0, inplace=True)
temp_df['BANANAS'] = ban_col

#temp_df['BANANAS'].value_counts()

temp_df["rating_category"] = temp_df["ORANGES"].apply(lambda x: 'good' if x >= 60 else 'bad')
temp_df.drop(columns=['ORANGES'], inplace=True)


print(temp_df)

