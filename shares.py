#!/usr/bin/python
# main part
import os
import pandas as pd
import datetime
# from datetime import date
from datetime import datetime
from datetime import timedelta

pd.core.common.is_list_like = pd.api.types.is_list_like

from pandas_datareader import data as web

import fix_yahoo_finance as yf

yf.pdr_override()  # <== that's all it takes :-)

# disable `warn` in pandas
pd.options.mode.chained_assignment = None


# choose execl file from menu
def choose_file():
    # get excel files from curent direcory
    list_xls = [f for f in os.listdir('./_input') if f.endswith('.xls') or f.endswith('.xlsx')]
    # print menu
    print '----------------------------------------------'
    print '--- program gets shares from Yahoo finance ---'
    print '---       ver. #2.06 ( 28.08.18 )          ---'
    print '----------------------------------------------'
    print ('\n\nFiles List:\n')
    for num, file_name in enumerate(list_xls):
        print ('{} - {}'.format(num + 1, file_name))
    print('***')

    file_number = 999999
    # choose file
    while file_number > len(list_xls):
        try:
            file_number = input('Enter file number or 0 for exit: ')
        except:
            print('\a')  # beep
        if file_number == 0:
            exit(1)

    return list_xls[file_number - 1]


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
    return table, symbl


# input shares dates
def get_date():
    date_entry = raw_input('Enter date in YYYY-MM-DD format: ')
    #    year, month, day = map(int, date_entry.split('-'))

    # !IMPORTANT! add 1 day to period, because `get` returns previous day
    return datetime.strptime(date_entry, '%Y-%m-%d') + timedelta(days=1)


# read and preproces shares from yahoo on current date
def read_shares(symbl, start, end):
    # read shares from `yahoo`
    shares_panel = web.get_data_yahoo(list(symbl), start, end)

    # convert Panel to the Multyindexed frame
    shares = shares_panel.to_frame()

    # remove index level 0 (data)
    shares.index = shares.index.droplevel(0)

    # convert index into column
    shares.reset_index(inplace=True)

    # rename `minor` column
    shares.rename(columns={'minor': 'SYMBOL'}, inplace=True)

    return shares


def create_output(table, shares, real_date):
    # remove unnesessary columns from shares
    # columns_to_drop = ['Close', 'High', 'Low', 'Open', 'Volume']
    shares.drop(['Close', 'High', 'Low', 'Open', 'Volume'], axis=1, inplace=True)

    # create `marged table
    table = pd.merge(left=table, right=shares, left_on='SYMBOL', right_on='SYMBOL')

    # rename some columns
    new_col_names = {'STOCKS': 'STOCKS-BUY', 'Unnamed: 10': 'STOCKS-SELL',
                     'CALLS': 'CALLS-BUY', 'Unnamed: 12': 'CALLS-SELL',
                     'PUTTES': 'PUTTES-BUY', 'Unnamed: 14': 'PUTTES-SELL'}
    table.rename(columns=new_col_names, inplace=True)

    # insert `CURRENT DATE` column before `ADJ price`
    table.insert(len(table.columns) - 1, 'CURRENT DATE', datetime.strftime(real_date, '%Y-%m-%d'))

    # add  and format calculated columns at the end of the table

    table['STRIKE UPSIDE'] = table['STRIKE UPSIDE %'] = None

    table.loc[table['TRX CODE'].str[0] == 'O', 'STRIKE UPSIDE'] = table['Adj Close'] - table['Strike  Price']
    table.loc[table['TRX CODE'].str[0] == 'E', 'STRIKE UPSIDE'] = table['Adj Close'] - table['BASIS COST']

    table.loc[table['TRX CODE'].str[0] == 'O', 'STRIKE UPSIDE %'] = table['STRIKE UPSIDE'] / table['Strike  Price']
    table.loc[table['TRX CODE'].str[0] == 'E', 'STRIKE UPSIDE %'] = table['STRIKE UPSIDE'] / table['BASIS COST']

    # write new xls table
    table.to_excel('./_output/' + file_name, index=False)


if __name__ == '__main__':
    '''Program enriches excel table with shares delivered from yahoo finance
    Use pandas module `datareader'. Original file is in _input directory,
    output excel file is in _output directory with the same name'''

    file_name = choose_file()
    start_date = end_date = get_date()
    table, symbl = create_table(file_name)  # create pandas df
    print('\n{} file choosen'.format(file_name))
    print 'work tables created...'
    shares = read_shares(symbl, start_date, end_date)  # deliver shares from yahoo
    if shares.empty:
        print '***\ncan not grab shares from yahoo-finance\ntry again in few minutes, please\n***'
    else:
        print ('shares delivered...')
        real_date = start_date + timedelta(days=-1)
        create_output(table, shares, real_date)  # create, format and write output xls
        print ('output file created')
