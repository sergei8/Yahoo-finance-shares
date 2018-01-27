#!/usr/bin/python
# main part
import os
import pandas as pd
import pandas_datareader.data as web
from datetime import date
from datetime import datetime
import datetime
from datetime import timedelta

pd.options.mode.chained_assignment = None  # disable `warn`

# choose execl file from menu
def choose_file():
    # get excel files from curent direcory
    list_xls = [f for f in os.listdir('./_input') if f.endswith('.xlsx')]
    # print menu
    print '----------------------------------------------'
    print '--- program gets shares from Yahoo finance ---'
    print '---       ver. #1.04 ( 01.26.18 )          ---'
    print '----------------------------------------------'
    print ('\n\nFiles List:\n')
    for num, file_name in enumerate(list_xls):
        print '{} - {}'.format(num + 1, file_name)
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
    table = table[pd.isnull(table.SYMBL) == False]
    
    # extract existing found-codes
    symbl = table.SYMBL.dropna().unique()
    
    return table, symbl  # return table and list of found market symbols


# input shares dates
def get_date():
    date_entry = raw_input('Enter date in YYYY-MM-DD format: ')
    year, month, day = map(int, date_entry.split('-'))
    return datetime.date(year, month, day)  # return datetime.datetime.now()


# read and preprocess shares from yahoo on current date
def read_shares(symbl, start, end):
    # start = end = datetime.datetime.now()
    # start = end = get_date()
    shares_panel = web.DataReader(symbl, 'yahoo', start, end)
    
    # convert Panel to the Multyindexed frame
    shares = shares_panel.to_frame()
    
    # remove yesterday (start_date -1) from multyindex df
    yesterday = start - timedelta(days=1)
    shares.drop(yesterday, level=0, axis=0, inplace=True)
    
    
    # remove index level 0 (data)
    shares.index = shares.index.droplevel(0)
    
    # convert index into column
    shares.reset_index(inplace=True)
    
    shares.rename(columns={'minor': 'symbl'}, inplace=True)
    
    # insert column
    shares['Current Date'] = start
    
    # remove column
    shares.drop(['Volume'], axis=1, inplace=True)
    
    return shares


# create output xls from table and shares dataframes
def create_output(table, shares):
    # create table
    table = pd.merge(left=table, right=shares, left_on='SYMBL', right_on='symbl')
    
    # delete 2-nd `symbol`
    table.drop('symbl', axis=1, inplace=True)
    
    # reformat date columns to m/d/y
    # table['Current Date'] = table['Current Date'].map(lambda x: x.strftime(format='%m/%d/%Y'))
    # table['EXP DATE'] = table['EXP DATE'].strftime('%m/%d/%Y')
    # table['EXP DATE'] = table['EXP DATE'].dt.strftime('%m/%d/%Y')
    
    # reformat prices to 2 dec.digits
    round_2 = lambda x: round(x, 2)
    table.Open = table.Open.map(round_2)
    table.Low = table.Low.map(round_2)
    table.High = table.High.map(round_2)
    table.Close = table.Close.map(round_2)
    table['Adj Close'] = table['Adj Close'].map(round_2)
    
    # reorder columns
    order = list(table.columns)[:-6]  # exept new columns
    new_order = order[:len(order)] + ['Current Date', 'Open', 'High', 'Low', 'Close', 'Adj Close']
    new_table = table[new_order]
    
    # reorder SEQ column through ass
    new_table.SEQ = range(1, new_table.SEQ.shape[0] + 1)
    
    # write new xls table
    new_table.to_excel('./_output/' + file_name, index=False)


if __name__ == '__main__':
    '''Program enriches excel table with shares delivered from yahoo finance
    Use pandas module `datareader'. Original file is in _input directory,
    output excel file is in _output directory with the same name'''
    
    file_name = choose_file()
    start_date = end_date = get_date()
    table, symbl = create_table(file_name)  # create pandas df
    print '\nwork tables created...'
    shares = read_shares(symbl, start_date, end_date)  # deliver shares from yahoo
    print 'shares delivered...'
    create_output(table, shares)  # create, reformat and write output xls
    print 'output file created'
