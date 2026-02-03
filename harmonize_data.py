import pandas as pd
import numpy as np
from datetime import datetime
import ast

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
    return any(ele.strip() in str(s).strip() for ele in dictionary[key])

def add_grounds(df, path, check_col, shortname):
    codes = {}
    codebook = pd.read_csv(path, header=None, index_col=0)
    for idx in codebook.index:
        codes['_'.join([shortname, idx])] = [s.strip() for s in list(codebook.loc[idx]) if s is not np.nan]

    for key in codes.keys():
        df[key] = df[check_col].apply(lambda s: description_check(s, codes, key))
    return df

def what_kind_of_record(row):
    tenant_ground = row['grounds_tenant']
    landlord_ground = row['grounds_landlord']
    
    # Check if the string representation of the list is not just '[]'
    has_tenant_ground = isinstance(tenant_ground, str) and tenant_ground.strip() != '[]'
    has_landlord_ground = isinstance(landlord_ground, str) and landlord_ground.strip() != '[]'

    if has_tenant_ground and not has_landlord_ground:
        return 'Tenant'
    elif not has_tenant_ground and has_landlord_ground:
        return 'Landlord'
    else:
        return 'Not classifiable'


def harmonize_data(input_file, output_file):
    df = pd.read_csv(input_file)

    # Clean header to get case_number and petition_number
    df['case_number'] = df['header'].str.split('\n', expand=True)[0].str.replace('CASE NUMBER:', '').str.strip()
    df['petition_number'] = df['header'].str.split('\n', expand=True)[1].str.replace('Petition Number:', '').str.strip()
    df['petition_number'] = pd.to_numeric(df['petition_number'], errors='coerce')


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
    df = add_grounds(df, 'codebooks/tenant_codebook.csv', 'grounds_tenant', 'ts')
    df = add_grounds(df, 'codebooks/landlord_codebook.csv', 'grounds_landlord', 'll')

    # Define final column order
    include_order = ['petition_number', 'case_number', 'apn', 'address_l1', 'address_l2',
                     'hearing_officer', 'program_analyst',
                     'date_filed', 'hearing_date', 'mediation_date', 'appeal_hearing_date',
                     'record_kind']
    landlord_cols = sorted([s for s in df.columns if 'll_' in s])
    tenant_cols = sorted([s for s in df.columns if 'ts_' in s])
    
    final_cols = include_order + landlord_cols + tenant_cols
    df = df[final_cols]

    df.to_csv(output_file, index=False)
    print(f"Harmonized data saved to {output_file}")
    print("\nFirst 5 rows of the harmonized data:")
    print(df.head())


if __name__ == '__main__':
    # Find the latest raw data file
    import os
    import glob
    list_of_files = glob.glob('./data_*.csv')
    latest_file = max(list_of_files, key=os.path.getctime)
    print(f"Harmonizing data from: {latest_file}")
    harmonize_data(latest_file, 'data_harmonized.csv')
