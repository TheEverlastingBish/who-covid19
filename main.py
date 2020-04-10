import os
import re
import json
import requests
from datetime import datetime
import numpy as np
import pandas as pd
import PyPDF2 as ppd
import tabula
import helper


def main():

    helper.prep()

    clean_links = helper.get_pdf_links()
    latest_link, latest_file, local_file = helper.get_latest_file(clean_links)
    print("Latest Link: {0}\nLatest File Basename: {1}\nLocal File Path:{2}".format(latest_link, latest_file, local_file))

    r = requests.get(latest_link, allow_redirects=True)

    with open(local_file, 'wb') as fl:
        fl.write(r.content)

    pdf_file_obj = open(local_file, 'rb')
    pdf_reader = ppd.PdfFileReader(pdf_file_obj)

    print("Total pages:", pdf_reader.numPages)

    # latest_pdf = r".\data\20200406-sitrep-77-covid-19.pdf"

    start_page = int(min(helper.get_page_range(pdf_reader, 'Western Pacific Region')))
    end_page = int(max(helper.get_page_range(pdf_reader, 'Subtotal for all'))) + 1
    print("Table Start Page: {}, Table End Page: {}".format(start_page, end_page))


    # Read PDF Tables
    df = helper.get_pdf_data(local_file, start_page, end_page)


    # Drop bad columns
    df = helper.drop_bad_columns(df)


    # Rename columns
    df.columns = helper.get_columns_labels()
    # df.to_csv(r".\data\before dropping rows.csv", header=True, encoding='utf-8', index=None)


    # Drop bad rows
    df = helper.drop_bad_rows(df)


    # Cleaning
    df['report_country'] = df['report_country'].astype('str')
    df.loc[df['report_country'].str.contains('Lao'), 'report_country'] = "Lao People's Democratic Republic"
    df = helper.clean_text(df)


    # Repopulate col1 with slid values from col2
    df.loc[(df['report_country'].isnull()) | (df['report_country'] == 'nan'), 'report_country'] = \
        df.loc[(df['report_country'].isnull()) | (df['report_country'] == 'nan'), 'confirmed']


    # Amend dtypes
    df['confirmed'] = df['confirmed'].apply(lambda x: pd.to_numeric(x, errors='coerce'))
    df['confirmed_new'] = df['confirmed_new'].apply(lambda x: pd.to_numeric(x, errors='coerce'))
    df['deaths'] = df['deaths'].apply(lambda x: pd.to_numeric(x, errors='coerce'))
    df['deaths_new'] = df['deaths_new'].apply(lambda x: pd.to_numeric(x, errors='coerce'))
    df['days_since_last_report'] = df['days_since_last_report'].apply(lambda x: pd.to_numeric(x, errors='coerce'))


    # More cleaning
    df.drop(df[(~df['report_country'].isin(helper.get_region_labels())) & \
               (df['confirmed'].isnull())].index, inplace=True)


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
    replacements = helper.get_replacements()

    df.replace(replacements, inplace=True)
    df.drop(df[df['report_country'].str.isnumeric()].index, inplace=True)

    df['report_date'] = helper.get_file_date(file_name=latest_file)

    df = df.loc[:, helper.get_final_column_order()]
    df.fillna(value=0, inplace=True)

    # Output
    output_file = helper.get_output_file(latest_file)
    print("Output saved at:", output_file)

    df.to_csv(output_file, header=True, encoding='utf-8', index=None)


if __name__ == '__main__':
    main()

