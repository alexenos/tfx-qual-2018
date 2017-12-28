#! /usr/bin/env python
# Dax Garner

"""
Web scraping utility for extracting data from the TFX 2018 Qualifier leaderboard. 
Reference: http://srome.github.io/Parsing-HTML-Tables-in-Python-with-BeautifulSoup-and-pandas/
"""

import requests
from bs4 import BeautifulSoup
import pandas as pd
import numpy as np
import re

# Parser Class
class TfxHTMLTableParser:

        def parse_url(self, url):
            response = requests.get(url)
            soup = BeautifulSoup(response.text, 'lxml')
            return self.parse_html_table(soup.find_all('table')[0])

        def parse_html_table(self, table):
            n_columns = 0
            n_columns_new = 0
            n_rows=0
            column_names = ['Athlete'] # Hack

            # Find number of rows and columns
            # we also find the column titles if we can
            for row in table.find_all('tr'):

                # Determine the number of rows in the table
                td_tags = row.find_all('td')
                if len(td_tags) > 0:
                    n_rows+=1
                    n_columns_new = len(td_tags)
                    if n_columns_new > n_columns:
                        # Set the number of columns for our table
                        n_columns = n_columns_new

                # Handle column names if we find them
                th_tags = row.find_all('th')
                if len(th_tags) > 0 and len(column_names) <= 1:
                    for th in th_tags:
                        column_names.append(th.get_text().strip())

            # Safeguard on Column Titles
            if len(column_names) > 0 and len(column_names) != n_columns:
                raise Exception("Column titles do not match the number of columns")

            columns = column_names if len(column_names) > 0 else range(0,n_columns)
            df = pd.DataFrame(columns = columns,
                              index= range(0,n_rows))
            row_marker = 0
            for row in table.find_all('tr'):
                column_marker = 0
                columns = row.find_all('td')
                for column in columns:
                    df.iat[row_marker,column_marker] = column.get_text().strip()
                    column_marker += 1
                if len(columns) > 0:
                    row_marker += 1
            return self.process_data(df.iloc[3:-1])

        def process_data(self, df):
            tfx = pd.DataFrame()
            tfx['Athlete'] = df['Athlete'].apply(lambda r: self.split_tfx_cell(r, 0))
            #print(tfx.head())
            tfx['Rank'] = df['Rank'].astype('int64')
            #print(df['Qualifier 1'])
            for i in range(6):
                tfx['Q' + str(i+1) + 'R'] = df['Qualifier ' + str(i+1)].apply(lambda r: float(self.split_tfx_cell(r, 0)))
                tfx['Q' + str(i+1) + 'S'] = df['Qualifier ' + str(i+1)].apply(lambda r: float(self.split_tfx_cell(r, 4)))
            #print(tfx.head())
            tfx['Total Score'] = df['Total Points'].apply(lambda r: self.int_tfx_cell(r, 0))
            #print(tfx.head())
            tfx['Gym'] = df['Athlete'].apply(lambda r: self.split_tfx_cell(r, 2))
            tfx = tfx.set_index('Athlete')
            #print(tfx.head())
            return tfx

        def split_tfx_cell(self, row, index):
            cell = row.split('\n')
            #print(len(cell), index)
            if len(cell) < index:
                return np.nan
            elif not cell[index]:
                return np.nan
            else:
                return row.split('\n')[index].strip()
        def int_tfx_cell(self, row, index):
            return int(re.findall('^\d+', self.split_tfx_cell(row, index))[0])

