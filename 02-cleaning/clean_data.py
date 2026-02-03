import pandas as pd
import numpy as np
from datetime import datetime
import ast
import os
import glob
import argparse

def clean_address(s):
    try:
        s = s.lower().strip()
        if s == '':
            return None
        else:
            return s
    except:
        if pd.isnull(s):
            return None

def make_timestamp(s):
    try:
        return datetime.strptime(s, '%m-%d-%Y')
    except:
        return np.nan

def description_check(s, dictionary, key):
    # Ensure s is a string before trying to split it
    if not isinstance(s, str):
        return False
    
    # The original notebook used a simple substring check, which is what's replicated here.
    # It checks if any of the codebook substrings are present in the grounds string.
    try:
        grounds_list = ast.literal_eval(s)
        for ground_dict in grounds_list:
            for term in dictionary[key]:
                if term in ground_dict.get('col_1', ''):
                    return True
    except (ValueError, SyntaxError):
        # Fallback for when the string is not a valid literal
        for term in dictionary[key]:
            if term in s:
                return True
    return False

def add_grounds(df, path, check_col, shortname):
    codes = {}
    codebook = pd.read_csv(path, header=None, index_col=0)
    for idx in codebook.index:
        # Use .iloc[:, 0] to get all values from the first column for that index
        codes['_'.join([shortname, idx])] = [s.strip() for s in codebook.loc[idx].dropna()]

    for key in codes.keys():
        df[key] = df[check_col].apply(lambda s: description_check(s, codes, key))
    return df

def what_kind_of_record(row):
    tenant_ground = row['grounds_tenant']
    landlord_ground = row['grounds_landlord']
    
    has_tenant_ground = isinstance(tenant_ground, str) and tenant_ground.strip() != '[]'
    has_landlord_ground = isinstance(landlord_ground, str) and landlord_ground.strip() != '[]'

    if has_tenant_ground and not has_landlord_ground:
        return 'Tenant'
    elif not has_tenant_ground and has_landlord_ground:
        return 'Landlord'
    else:
        return 'Not classifiable'


def clean_data(input_file, output_file):
    df = pd.read_csv(input_file)

    # Clean header and petition number
    header_split = df['header'].str.split('\\n', expand=True)
    df['case_number'] = header_split[0].str.replace('CASE NUMBER:', '').str.strip()
    
    # Extract petition number from "Tenant: 12345" or "Property Owner: 12345"
    if 'petition_number' in df.columns:
        df['petition_number'] = df['petition_number'].str.split(':', expand=True)[1].str.strip()
    
    # df['petition_number'] = pd.to_numeric(df['petition_number'], errors='coerce') # Removed to keep as string

    # Clean address
    df['address'] = df['address'].apply(clean_address)
    df['address_l1'] = df['address'].str.split('\n|,|apt.|apt|#', expand=True)[0].apply(clean_address)
    df['address_l2'] = df['address'].str.split('\n|,|apt.|apt|#', expand=True)[1].apply(clean_address)

    # Clean dates
    for col in ['date_filed', 'hearing_date', 'mediation_date', 'appeal_hearing_date']:
        df[col] = df[col].apply(make_timestamp)

    # Create record_kind
    df['record_kind'] = df.apply(what_kind_of_record, axis=1)

    # Add grounds columns
    df = add_grounds(df, './codebooks/tenant_codebook.csv', 'grounds_tenant', 'ts')
    df = add_grounds(df, './codebooks/landlord_codebook.csv', 'grounds_landlord', 'll')

    # Define final column order
    include_order = ['petition_number', 'case_number', 'apn', 'address_l1', 'address_l2',
                     'hearing_officer', 'program_analyst',
                     'date_filed', 'hearing_date', 'mediation_date', 'appeal_hearing_date',
                     'record_kind']
    landlord_cols = sorted([s for s in df.columns if 'll_' in s])
    tenant_cols = sorted([s for s in df.columns if 'ts_' in s])
    
    final_cols = include_order + landlord_cols + tenant_cols
    # Filter out columns that don't exist in the dataframe
    final_cols = [col for col in final_cols if col in df.columns]
    df = df[final_cols]

    df.to_csv(output_file, index=False)
    print(f"Cleaned data saved to {output_file}")
    print("\nFirst 5 rows of the cleaned data:")
    print(df.head())


import argparse

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description="Clean RAP case data.")
    parser.add_argument('--file', type=str, help='The absolute path to the raw data file to be cleaned.')
    args = parser.parse_args()

    if args.file:
        latest_file = args.file
    else:
        # Find the latest raw data file in the ./data/raw directory
        list_of_files = glob.glob('./data/raw/data_*.csv')
        if not list_of_files:
            print("No raw data files found in ./data/raw/")
            exit()
        else:
            # Function to extract end date from filename
            def get_end_date(filepath):
                try:
                    # Filename format is data_MMDDYYYY_MMDDYYYY.csv
                    date_str = os.path.basename(filepath).split('_')[2].split('.')[0]
                    return datetime.strptime(date_str, '%m%d%Y')
                except (IndexError, ValueError):
                    # Return a very old date if parsing fails
                    return datetime.min

            # Find the file with the most recent end date
            latest_file = max(list_of_files, key=get_end_date)

    print(f"Cleaning data from: {latest_file}")
    
    # Create a filename for the cleaned data
    base_filename = os.path.basename(latest_file)
    cleaned_filename = f"cleaned_{base_filename}"
    output_path = os.path.join('./data/cleaned', cleaned_filename)
    
    clean_data(latest_file, output_path)