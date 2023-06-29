import pandas as pd
import os

# Path to the directory containing the XLSX files
directory = './subtitles'

# Get a list of all XLSX files in the directory
xlsx_files = [file for file in os.listdir(directory) if file.endswith('.xlsx')]

# Create an empty DataFrame to store the merged data
merged_data = pd.DataFrame()

# Iterate over each XLSX file
for file in xlsx_files:
    # Read the XLSX file into a DataFrame
    df = pd.read_excel(os.path.join(directory, file))
    
    # Concatenate the DataFrame with the merged_data DataFrame
    merged_data = pd.concat([merged_data, df], ignore_index=True)

# Path and filename for the combined CSV file
combined_csv_file = 'Combined transcript.csv'

# Write the merged_data DataFrame to a CSV file
merged_data.to_csv(combined_csv_file, index=False)

print(f"Successfully merged {len(xlsx_files)} XLSX files into {combined_csv_file}.")
