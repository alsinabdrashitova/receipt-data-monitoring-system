# -*- coding: utf-8 -*-
import pandas as pd
import string
import numpy as np
import csv
from io import StringIO

from sqlalchemy import create_engine

import warnings
warnings.simplefilter(action='ignore', category=FutureWarning)


def to_delete(df):
    df['items.name'] = df['items.name'].str.lower()

    toDelete = (df['items.name'].str.contains('электро') == False) & (
            df['items.name'].str.contains('проезд') == False) & (df['items.name'].str.contains('игры') == False) & (
                       df['items.name'].str.contains('домен') == False) & (
                       df['items.name'].str.contains('гвс') == False) & (
                       df['items.name'].str.contains('перевозка') == False) & (
                       df['items.name'].str.contains('кпг') == False) & (
                       df['items.name'].str.contains('лицензи') == False) & (
                       df['items.name'].str.contains('тко') == False) & (
                       df['items.name'].str.contains('поездк') == False) & (
                       df['items.name'].str.contains('подписк') == False) & (
                       df['items.name'].str.contains('жку') == False) & (
                       df['items.name'].str.contains('билет') == False) & (
                       df['items.name'].str.contains('ремень') == False) & (
                       df['items.name'].str.contains('24 часа') == False) & (
                       df['items.name'].str.contains('бензин') == False) & (
                       df['items.name'].str.contains('аи-9') == False) & (
                       df['items.name'].str.contains('наушники') == False) & (
                       df['items.name'].str.contains('русское издание') == False) & (
                       df['items.name'].str.contains('колодки') == False) & (
                       df['items.name'].str.contains('рулевая') == False) & (
                       df['items.name'].str.contains('аб раб на') == False) & (
                       df['items.name'].str.contains('бик мак') == False) & (
                       df['items.name'].str.contains('бизнес стандарт') == False) & (
                       df['items.name'].str.contains('бургер') == False) & (
                       df['items.name'].str.contains('водоотведение') == False) & (
                       df['items.name'].str.contains('тара') == False) & (
                       df['items.name'].str.contains('дт-') == False) & (
                       df['items.name'].str.contains('звезды') == False) & (
                       df['items.name'].str.contains('платёж') == False) & (
                       df['items.name'].str.contains('кошелек') == False) & (
                       df['items.name'].str.contains('нап. ср.') == False) & (
                       df['items.name'].str.contains('отопление') == False) & (
                       df['items.name'].str.contains('позиция') == False) & (
                       df['items.name'].str.contains('пополнение') == False) & (
                       df['items.name'].str.contains('ставк') == False) & (
                       df['items.name'].str.contains('приход') == False) & (
                       df['items.name'].str.contains('багаж') == False) & (
                       df['items.name'].str.contains('разовый') == False) & (
                       df['items.name'].str.contains('спорт') == False) & (
                       df['items.name'].str.contains('суг') == False) & (
                       df['items.name'].str.contains('товар') == False) & (
                       df['items.name'].str.contains('трк') == False) & (
                       df['items.name'].str.contains('удержание') == False) & (
                       df['items.name'].str.contains('виагра') == False) & (
                       df['items.name'].str.contains('услуг') == False)
    df = df[toDelete]

    df = df.sort_values(by='items.name')
    df = df.iloc[2:]

    df['items.name'] = df['items.name'].replace(r'[{}]'.format(string.punctuation), '', regex=True)
    df['items.name'] = df['items.name'].str.replace('\d+', '')

    return df


def word_delete(df):
    i = 0
    list_of_sentance = []
    for sentance in df['items.name'].to_numpy():
        list_of_sentance.append(sentance.split())

    new_table = []
    for line in list_of_sentance:
        new_line = []
        for word in line:
            if len(word) > 2:
                new_line.append(word)
        new_table.append(' '.join(new_line))

    data = pd.DataFrame(new_table, columns=['items.name'])
    data['items.price'] = pd.Series(df['items.price'].to_numpy())
    data['items.quantity'] = pd.Series(df['items.quantity'].to_numpy())

    return data


def price_formatting(df):
    for index, price in enumerate(list(df['items.price'])):
        df.loc[index, 'items.price'] = float(int(price) / 100)

    return df


def data_generation(df, count):
    new_df = df.copy()
    for i in range(count):
        new_df = new_df.append(df.sample())

    return new_df


def psql_insert_copy(table, conn, keys, data_iter):
    print(conn)
    dbapi_conn = conn.connection
    with dbapi_conn.cursor() as cur:
        s_buf = StringIO()
        writer = csv.writer(s_buf)
        writer.writerows(data_iter)
        s_buf.seek(0)

        columns = ', '.join('"{}"'.format(k) for k in keys)
        if table.schema:
            table_name = '{}.{}'.format(table.schema, table.name)
        else:
            table_name = table.name

        sql = 'COPY {} ({}) FROM STDIN WITH CSV'.format(
            table_name, columns)
        cur.copy_expert(sql=sql, file=s_buf)


if __name__ == '__main__':
    data = pd.read_csv('project/data/data_minprom.csv', delimiter=',',
                       names=['receiptCode', 'fiscalDocumentNumber', 'dateTime', 'shiftNumber', 'requestNumber',
                              'operationType', 'totalSum', 'items.name', 'items.price', 'items.quantity', 'items.sum',
                              'items.ndsNo', 'cashTotalSum', 'ecashTotalSum', 'taxationType', 'ndsNo'])

    data = data.drop(
        ['receiptCode', 'fiscalDocumentNumber', 'dateTime', 'shiftNumber', 'requestNumber', 'operationType', 'totalSum',
         'items.sum', 'items.ndsNo', 'cashTotalSum', 'ecashTotalSum', 'taxationType', 'ndsNo'], axis=1)

    data = pd.DataFrame(data)
    data = to_delete(data)
    data = word_delete(data)
    data = price_formatting(data)
    data = data_generation(data, 5000)

    engine = create_engine("postgresql://db:123456@postgres:5432/db")
    sql = 'DROP TABLE IF EXISTS mlflow_clope;'
    engine.execute(sql)
    data.to_sql('mlflow_clope', engine, method=psql_insert_copy)

    print(data)
