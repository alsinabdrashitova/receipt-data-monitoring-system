# -*- coding: utf-8 -*-
import pandas as pd
import string
import numpy as np
import csv
from io import StringIO
import re
from sqlalchemy import create_engine

import warnings
warnings.simplefilter(action='ignore', category=FutureWarning)


def selected_brands(str):
    results = {}
    with open('project/data/brands_7841.txt', encoding = 'utf-8') as file:
        f = file.read()
        f = f.lower()
        f = f.split('\n')
        data_map = {}
        for line in f:
            l = line.split(' ')
            arr = data_map.get(l[0], [])
            arr.append(line)
            data_map[l[0]] = arr

    def get_line_brand(line_arr, str_l):
        for word in line_arr:
            r = data_map.get(word, False)
            if r:
                for br in r:
                    if br in str_l:
                        return br

    arr = str
    result = []
    for line in arr:
        str_line = ' '.join(line)
        brand = get_line_brand(line, str_line)
        if brand:
            new_line = ' '.join(str_line.split(brand))
            new_line = new_line.replace('  ', ' ').strip()
            result.append([new_line, brand])
        else:
            result.append([str_line, 'не определено'])
    return result


def make_trans():
    a = 'a b c d e f g h i j k l m n o p q r s t u v w x y z ё'.split()
    b = 'а в с д е ф г н и ж к л м н о п к р с т у в в х у з е'.split()
    trans_dict = dict(zip(a, b))
    trans_table = ''.join(a).maketrans(trans_dict)
    return trans_table


def normalize(ser: pd.Series):
#   "СокДобрый" -> "Сок Добрый"
    camel_case_pat = re.compile(r'([а-яa-z])([А-ЯA-Z])')
#   "lmno" -> "лмно"
    trans_table = make_trans()
#   "15 мл" -> "15мл"
    unit = 'мг|г|гр|кг|мл|л|шт'
    unit_pat = re.compile(fr'((?:\d+p)?\d+)\s*({unit})\b')
#   "ж/б ст/б" -> "жб стб"
    w_w_pat = re.compile(r'\b([а-я]{1,2})/([а-я]{1,2})\b')


    return ser \
            .str.replace(camel_case_pat, r'\1 \2') \
            .str.lower() \
            .str.translate(trans_table) \
            .str.replace(unit_pat, r' \1\2 ') \
            .str.replace(w_w_pat, r' \1\2 ')


def data_extraction(product_name):
    value1 = []
    vol = []
    for i in product_name:
        char = re.findall('(\d+)(кг|г|гр|к|л|мл|мг)', i)
        if char:
            value1.append(char)
        else:
            value1.append(['', ''])
    for i in value1:
        vol.append(i[0])

    value1 = []
    count = []
    for i in product_name:
        char = re.findall('(\d+)(шт)', i)
        if char:
            #       a = char.group(1)
            value1.append(char)
        else:
            value1.append([''])
    for i in value1:
        count.append(i[0])

    value2 = []
    percent = []
    for i in product_name:
        char = re.findall('(\d+|\d+.\d+)(%)', i)
        if char:
            #       a = char.group(1)
            value2.append(char)
        else:
            value2.append(['', ''])
    for i in value2:
        percent.append(i[0])
    print(vol)
    print(count)
    print(percent)
    return vol, count, percent


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
    data = pd.read_csv('project/data/train.csv')
    # data = pd.read_csv('train.csv')
    data['items.name'] = data['name']
    data = data.dropna()
    name = data['name'].to_numpy()
    price = data['price'].to_numpy()
    count = data['count'].to_numpy()
    items_name = data['items.name'].to_numpy()

    data['items.name'] = data['items.name'].str.lower()
    data['items.name'] = data['items.name'].str.replace('.', ' ')
    data['items.name'] = data['items.name'].str.replace('/', ' ')
    nmp = data['items.name'].to_numpy()
    list_of_sentance = []
    for sentance in nmp:
        list_of_sentance.append(sentance.split())
    for name in [data]:
        name['items.name'] = normalize(name['items.name'])
    brands = selected_brands(list_of_sentance)
    df_brands = pd.DataFrame(brands, columns=['names', 'brand'])
    data['brand'] = df_brands['brand']

    vol, count, percent = data_extraction(items_name)
    print(vol)
    vol = pd.DataFrame(vol, columns=['volume', 'единица'])
    data['volume'] = vol['volume']

    new = pd.DataFrame(count, columns=['count'])
    new['count'] = new['count'].astype(str)
    new['count'] = new['count'].replace(r'[{}]'.format(string.punctuation), '', regex=True)
    data['quantity'] = new['count']

    percent = pd.DataFrame(percent, columns=['Процент'])
    percent['Процент'] = percent['Процент'].astype(str)
    percent['Процент'] = percent['Процент'].replace(r'[{}]'.format(string.punctuation), '', regex=True)
    data['percent'] = percent['Процент']
    data['percent'] = data['percent'].str.replace(' ', ',')
    data['percent'] = data['percent'].str.replace('-', ',')

    data = data.fillna(0)
    data['items.name'] = data['items.name'].str.replace('\d+', '')
    data['items.name'] = data['items.name'].replace(r'[{}]'.format(string.punctuation), '', regex=True)
    data['items.name'] = data['items.name'].apply(lambda x: re.sub(' +', ' ', str(x)))

    nmp = data['items.name'].to_numpy()
    list_of_sentance = []
    for sentance in nmp:
        list_of_sentance.append(sentance.split())
    new_table = []
    for line in list_of_sentance:
        new_line = []
        for word in line:
            if len(word) > 2:
                new_line.append(word)
        new_table.append(' '.join(new_line))

    data.drop(columns=['items.name'], axis=1)
    data['items.name'] = pd.DataFrame(new_table)
    data = data.sort_values(by='items.name')
    data = data.drop(
        labels=[2852, 69, 70, 71, 72, 73, 74, 9116, 9018, 9017, 9016, 9015, 9014, 3083, 11714, 10563, 2990, 1041, 9779,
                2280, 8361, 12436, 1968, 12511, 11801, 1673, 1343], axis=0)


    engine = create_engine("postgresql://db:123456@postgres:5432/db")
    sql = 'DROP TABLE IF EXISTS mlflow_clope;'
    engine.execute(sql)
    data.to_sql('mlflow_clope', engine, method=psql_insert_copy)
    print(data)
