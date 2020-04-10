# Helper File
# @Author: Bish Sinha, Data Buddha

import os
import re
import requests
from datetime import datetime
import numpy as np
import pandas as pd
import tabula
from bs4 import BeautifulSoup
from config import AppConfig


app_config = AppConfig()


def prep():
    app_config.initialize()


def get_pdf_links():
    html_content = requests.get(app_config.URL).text
    soup = BeautifulSoup(html_content, "html.parser")

    pdf_links = []
    for a in soup.find_all('a', attrs = {"target": "_blank"}):
        sr = re.search('.*situation-report.*', a['href'])
        if sr:
            pdf_links.append(a['href'])

    clean_links = ['https://www.who.int' + a for a in pdf_links]
    return clean_links


def get_latest_file(pdf_links):

    latest_pdf_link = pdf_links[0]
    latest_file_name = os.path.basename(latest_pdf_link).split('.pdf')[0]

    local_pdf_file_name = os.path.join(app_config.data_dir, latest_file_name + '.pdf')
    # print(local_pdf_file_name)

    return latest_pdf_link, latest_file_name, local_pdf_file_name


def get_page_range(pdf_reader_object, search_word):
    search_result_pages = []
    search_word_count = 0

    for page_num in range(1, pdf_reader_object.numPages):
        page_obj = pdf_reader_object.getPage(page_num)
        text = page_obj.extractText()
        search_text = text.split('\n')
        for line in search_text:
            if search_word in line:
                search_word_count += 1
                search_result_pages.append(page_num)

    return search_result_pages


def get_pdf_data(local_pdf_file, start_page, end_page):
    dfs = tabula.read_pdf(local_pdf_file,
                          pages="{0}-{1}".format(start_page, end_page),
                          multiple_tables=True,
                          output_format='dataframe',
                          pandas_options={'encoding': 'utf-8', 'header': None})

    print("Tables found:", len(dfs))

    # Generate Combined Pandas DF
    df = pd.concat(dfs, ignore_index=True)
    return df


def drop_bad_rows(df):
    first_row = int(min(df[df['report_country'].isin(['Western Pacific Region', 'estern Pacific Region'])].index.values))
    last_row = int(min(df[df['report_country'].isin(['Subtotal for all', 'ubtotal for all'])].index.values))

    df.drop(df[df['report_country'].isin(app_config.bad_rows)].index, inplace=True)
    df.drop(df[df['confirmed'].isin(app_config.bad_rows)].index, inplace=True)

    top_rows_to_del = [i for i in range(first_row) if i in df.index]
    bottom_rows_to_del = [i for i in range(last_row, len(df)) if i in df.index]
    rows_to_del = list(set(top_rows_to_del + bottom_rows_to_del))

    df = df.drop(rows_to_del).reset_index(drop=True)

    return df


def drop_bad_columns(df):
    cols = df.columns.values
    expected_cols = range(7)
    cols_to_del = list(set(cols) - set(expected_cols))

    if len(df) > 6:
        df.drop(columns=cols_to_del, inplace=True)

    return df


def trim_whitespace(x):
    clean_string = re.sub(r"\[1\]", "", x).strip() if isinstance(x, str) else x
    return clean_string


def clean_text(df):
    """
    Trim whitespace from ends of each value across all series in dataframe
    Do further custom cleanings
    """

    df.replace(r"\*", "", regex=True, inplace=True)
    df.replace(r"\n", ' ', regex=True, inplace=True)
    df.replace(r"\r", ' ', regex=True, inplace=True)

    # clean_string = trim_whitespace(df)
    # clean_string = lambda x: re.sub(r"\[1\]", "", x).strip() if isinstance(x, str) else x
    return df.applymap(trim_whitespace)


def get_columns_labels():
    return app_config.data_columns['column_labels']


def get_region_labels():
    return app_config.data_columns['region_labels']


def get_replacements():
    return app_config.data_columns['replacements']


def get_file_date(file_name):
    file_date = datetime.strptime(re.match('\d{8}', file_name).group(), "%Y%m%d")
    return file_date


def get_final_column_order():
    return app_config.data_columns['final_column_order']


def get_output_file(latest_file):
    output_file_name = os.path.join(app_config.data_dir, latest_file + '.csv')
    return output_file_name

