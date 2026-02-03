import pandas as pd
import ast

def get_unique_grounds(file_path):
    df = pd.read_csv(file_path)
    unique_grounds = set()

    for col in ['grounds_tenant', 'grounds_landlord']:
        for item in df[col].dropna():
            try:
                grounds_list = ast.literal_eval(item)
                for ground in grounds_list:
                    if 'col_1' in ground:
                        unique_grounds.add(ground['col_1'])
            except (ValueError, SyntaxError) as e:
                print(f"Could not parse value: {item}, Error: {e}")

    print("Unique grounds found:")
    for ground in sorted(list(unique_grounds)):
        print(f"- {ground}")

if __name__ == '__main__':
    get_unique_grounds('data_09012025_11012025.csv')
