import pandas as pd

# Load the csv file
df = pd.read_csv('../output.csv')

# Create a mask for non-empty values in 'Narrator', 'FilePath', 'Language', and 'Timecode Range'
mask = df[['Narrator', 'FilePath', 'Language', 'Timecode Range']].notnull().all(axis=1)

# Only apply groupby to rows where 'Narrator', 'FilePath', 'Language', and 'Timecode Range' are not empty
df.loc[mask, 'Text'] = df[mask].groupby(['Narrator', 'FilePath', 'Language', 'Timecode Range'])['Text'].transform(lambda x : ' '.join(x))

# Remove duplicates
df = df.drop_duplicates()

# Write the dataframe back to csv
df.to_csv('../merged.csv', index=False)
