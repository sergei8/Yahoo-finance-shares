#!/usr/bin/python
# main part
import os
import pandas as pd
# import datetime
# from datetime import date
from datetime import datetime
from datetime import timedelta

pd.core.common.is_list_like = pd.api.types.is_list_like

from pandas_datareader import data as web

import fix_yahoo_finance as yf

yf.pdr_override()  # <== that's all it takes :-)

# disable `warn` in pandas
pd.options.mode.chained_assignment = None


# choose excel file list
def get_files_list():
    # get excel files from curent direcory
    files_list = [file_name for file_name in os.listdir('./_input') if file_name.endswith('.xls')
                  or file_name.endswith('.xlsx')]
    # print(files_list)
    return files_list


# read xls into pandas table
def create_table(file_name):
    tables_list = pd.read_excel('./_input/' + file_name, sheetname=None)
    
    # get last worksheet from list
    table = tables_list[tables_list.keys()[-1]]
    
    # clear nan rows
    table = table[pd.isnull(table.SYMBOL) == False]
    
    # extract existing found-codes
    symbl = table.SYMBOL.dropna().unique()
    
    # return table and list of found market symbols
    return table, list(symbl)


# read and preproces shares from yahoo on current date
def read_shares(symbols_list, shares_date):
    # read shares from `yahoo`
    shares_panel = web.get_data_yahoo(symbols_list, shares_date, shares_date)
    
    # convert Panel to the Multyindexed frame
    shares = shares_panel.to_frame()
    
    # remove index level 0 (data)
    shares.index = shares.index.droplevel(0)
    
    # convert index into column
    shares.reset_index(inplace=True)
    
    # rename `minor` column
    shares.rename(columns={'minor': 'SYMBOL'}, inplace=True)
    
    return shares


# create output xls from table and shares dataframes
def create_output(table, file_name, shares, current_date):
    # remove unnesessary columns from shares
    columns_to_drop = ['Close', 'High', 'Low', 'Open', 'Volume']
    shares_tmp = shares.drop(columns_to_drop, axis=1)
    
    # create table
    table = pd.merge(left=table, right=shares_tmp, left_on='SYMBOL', right_on='SYMBOL')
    
    # rename some columns
    new_col_names = {'STOCKS': 'STOCKS-BUY', 'Unnamed: 10': 'STOCKS-SELL',
                     'CALLS': 'CALLS-BUY', 'Unnamed: 12': 'CALLS-SELL',
                     'PUTTES': 'PUTTES-BUY', 'Unnamed: 14': 'PUTTES-SELL'}
    table.rename(columns=new_col_names, inplace=True)
    
    # insert `CURRENT DATE` column before `ADJ price`
    table.insert(len(table.columns) - 1, 'CURRENT DATE', current_date.strftime('%m-%d-%Y'))
    
    # add  and format calculated columns at the end of the table
    table['STRIKE UPSIDE'] = table['Adj Close'] - table['Strike  Price']
    table['STRIKE UPSIDE %'] = table['STRIKE UPSIDE'] / table['Strike  Price']
    
    # write new xls table
    table.to_excel('./_output/' + file_name, index=False)


# create symbols_list from all symbols in files_list
def get_symbols_list(files_list):
    symbols_list = []
    for file_name in files_list:
        __, symbols = create_table(file_name)
        for symbol in symbols:
            if symbol not in symbols_list:
                symbols_list.append(symbol)
    return symbols_list


if __name__ == '__main__':
    '''Program enriches excel table with shares delivered from yahoo finance
    Use pandas module `datareader'. Original file is in _input directory,
    output excel file is in _output directory with the same name'''
    
    # get xls-files from `_input` folder
    files_list = get_files_list()
    # print files_list
    
    # set date for get shares as for previous day
    shares_date = datetime.now() + timedelta(-3)
    print 'shares on: ' + str(shares_date)
    
    # get list of `symbol`
    symbols_list = get_symbols_list(files_list)
    print('symbols: ' + ','.join(symbols_list))
    
    # deliver shares of `symbols_list` from `yahoo finance`
    # return dataframe `shares`
    shares = read_shares(symbols_list, shares_date)
    # print shares.head(3)
    
    # if shares have grabbed then continue
    if not shares.empty:
        for file_xls in files_list:
            tbl = create_table(file_xls)[0]
            try:
                create_output(tbl, file_xls, shares, shares_date)
            except KeyError:
                print 'error processing file ' + file_xls
        print('\noutput files created:')
        print('---------------------')
        for file_names in files_list:
            print(file_names)
    else:
        print '***\ncan not grab shares from yahoo-finance\ntry again in few minutes, please\n***'
