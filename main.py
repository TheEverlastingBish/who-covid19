import os
import re
import json
import requests
from datetime import datetime
import numpy as np
import pandas as pd
import PyPDF2 as ppd
import tabula
from bs4 import BeautifulSoup


# Prep
repo_dir = os.path.dirname(os.path.abspath(__file__))
data_dir = os.path.join(repo_dir, 'data')

if not os.path.exists(data_dir):
    os.mkdir(data_dir)


# Web
url = r"https://www.who.int/emergencies/diseases/novel-coronavirus-2019/situation-reports"
html_content = requests.get(url).text
soup = BeautifulSoup(html_content, "html.parser")


pdf_links = []
for a in soup.find_all('a', attrs = {"target": "_blank"}):
    sr = re.search('.*situation-report.*', a['href'])
    if sr:
        pdf_links.append(a['href'])

clean_links = ['https://www.who.int' + a for a in pdf_links]
latest_pdf_link = clean_links[0]
latest_file_name = os.path.basename(latest_pdf_link).split('.pdf')[0]

local_pdf_file = os.path.join(r".\data", latest_file_name + '.pdf')
print(local_pdf_file)

r = requests.get(latest_pdf_link, allow_redirects=True)

with open(local_pdf_file, 'wb') as fl:
    fl.write(r.content)

pdf_file_obj = open(local_pdf_file, 'rb')
pdf_reader = ppd.PdfFileReader(pdf_file_obj)

print(pdf_reader.numPages)

def get_page_range(pdf_reader_object, search_word):

    search_result_pages = []
    search_word_count = 0

    for pageNum in range(1, pdf_reader_object.numPages):
        pageObj = pdf_reader_object.getPage(pageNum)
        text = pageObj.extractText()
        search_text = text.split('\n')
        for line in search_text:
            if search_word in line:
                search_word_count += 1
                search_result_pages.append(pageNum)
    
    return search_result_pages

# latest_pdf = r".\data\20200406-sitrep-77-covid-19.pdf"

print("Latest PDF Link:", local_pdf_file)

start_page = min(get_page_range(pdf_reader, 'Western Pacific Region'))
end_page   = min(get_page_range(pdf_reader, 'Subtotal for all'))

print("Start Page: {}, End Page: {}".format(start_page, end_page))




# Read PDF Tables
dfs = tabula.read_pdf(local_pdf_file, 
                      pages="{}-{}".format(start_page, end_page), 
                      multiple_tables=True, 
                      output_format='dataframe', 
                      pandas_options={'encoding': 'utf-8', 'header': None})

print("Tables found:", len(dfs))


# Generate Combined Pandas DF
df = pd.concat(dfs, ignore_index=True)



# Drop bad rows
first_row = int(df[df[0] == 'Western Pacific Region'].index.values)
rows_to_del = range(first_row)

df = df.drop(rows_to_del).reset_index(drop=True)



# Drop bad columns
cols = df.columns.values
expected_cols = range(7)
cols_to_del = list(set(cols) - set(expected_cols))

if len(df) > 6:
    df.drop(columns=cols_to_del, inplace=True)

# Rename columns
df.columns = ['report_country', 
              'confirmed', 
              'confirmed_new', 
              'deaths', 
              'deaths_new', 
              'trans_class', 
              'days_since_last_report']


df.drop(df[df['report_country'].isin(['Subtotal for all', 'regions', 'Grand total', 'International', 'conveyance (Diamond'])].index, inplace=True)
df.drop(df[df['confirmed'].isin(['Subtotal for all', 'regions', 'Grand total'])].index, inplace=True)



# Cleaning
df['report_country'] = df['report_country'].astype('str')

df.loc[(df['report_country'] == 'conveyance (Diamond'), 'report_country'] = 'International conveyance (Diamond Princess)'
df.loc[df['report_country'].str.contains('Lao'), 'report_country'] = "Lao People's Democratic Republic"


def clean_text(df):
    """
    Trim whitespace from ends of each value across all series in dataframe
    Do further custom cleanings
    """

    df.replace(r"\*", "", regex=True, inplace=True)
    df.replace(r"\n", ' ', regex=True, inplace=True)
    df.replace(r"\r", ' ', regex=True, inplace=True)

    clean_string = lambda x: re.sub(r"\[1\]", "", x).strip() if isinstance(x, str) else x
    return df.applymap(clean_string)

df = clean_text(df)



# Repopulate col1 with slid values from col2
df.loc[(df['report_country'].isnull()) | (df['report_country'] == 'nan'), 'report_country'] = df.loc[(df['report_country'].isnull()) | (df['report_country'] == 'nan'), 'confirmed']



# Amend dtypes
df['confirmed'] = df['confirmed'].apply(lambda x: pd.to_numeric(x, errors='coerce'))
df['confirmed_new'] = df['confirmed_new'].apply(lambda x: pd.to_numeric(x, errors='coerce'))

df['deaths'] = df['deaths'].apply(lambda x: pd.to_numeric(x, errors='coerce'))
df['deaths_new'] = df['deaths_new'].apply(lambda x: pd.to_numeric(x, errors='coerce'))

df['days_since_last_report'] = df['days_since_last_report'].apply(lambda x: pd.to_numeric(x, errors='coerce'))

region_labels = ['Western Pacific Region', 
                 'European Region', 
                 'South-East Asia Region', 
                 'Eastern Mediterranean Region', 
                 'Region of the Americas', 
                 'African Region', 
                 'Territories',
                 'estern Pacific Region', 
                 'uropean Region', 
                 'outh-East Asia Region', 
                 'astern Mediterranean Region', 
                 'egion of the Americas', 
                 'frican Region', 
                 'erritories']

df.drop(df[(~df['report_country'].isin(region_labels)) & (df['confirmed'].isnull())].index, inplace=True)


# Generate Region
df['region'] = df.loc[(df['confirmed'].isnull()) & (~df['report_country'].isin(['Territories', 'erritories'])), 'report_country']
df['region'] = df['region'].fillna(method='ffill')




# Extract Territories
df['location_type'] = np.nan
df.loc[df['report_country'].isin(['Territories', 'erritories']), 'location_type'] = 'Territory'

df.loc[0, 'location_type'] = df.loc[0, 'report_country']
df.loc[df['region'] != df['region'].shift(1), 'location_type'] = df['region']
df['location_type'].fillna(method='ffill', inplace=True)

df.loc[~df['location_type'].isin(['Territory', 'erritories']), 'location_type'] = 'Nation'
df.dropna(subset=['report_country', 'confirmed'], inplace=True)
df.drop(df[df['report_country'] == 'nan'].index, inplace=True)




# Final Cleaning
with open(r".\replacements.json", "r") as json_repls:
    repls = json.load(json_repls)

df.replace(repls, inplace=True)
df.drop(df[df['report_country'].str.isnumeric()].index, inplace=True)


file_date = datetime.strptime(re.match('\d{8}', latest_file_name).group(), "%Y%m%d")
df['report_date'] = file_date

new_order = ['report_date', 'region', 'location_type', 'report_country', 'confirmed', 'confirmed_new', 'deaths', 'deaths_new', 'trans_class', 'days_since_last_report']

df = df.loc[:, new_order]
df.fillna(value=0, inplace=True)




# Output
output_file_name = latest_file_name + '.csv'
output_file = os.path.join(data_dir, output_file_name)
print(output_file)

df.to_csv(output_file, header=True, encoding='utf-8', index=None)
