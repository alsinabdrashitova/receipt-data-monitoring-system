from __future__ import print_function
import os
import argparse

import mlflow
import pandas as pd
import numpy as np
import psycopg2
import csv
from io import StringIO
import mlflow.sklearn
import sklearn

from mlflow import log_metric, log_param, log_artifacts, active_run
from clope import CLOPE
from sqlalchemy import create_engine

os.environ["AWS_DEFAULT_REGION"] = "eu-west-3"
os.environ["AWS_REGION"] = "eu-west-3"
os.environ["AWS_ACCESS_KEY_ID"] = "admin"
os.environ["AWS_SECRET_ACCESS_KEY"] = "adminadmin"
os.environ["MLFLOW_S3_ENDPOINT_URL"] = "http://minio:9000"


def db_connection():
    con = psycopg2.connect(
        database="db",
        user="db",
        password="123456",
        host="postgres",
        port="5432"
    )

    cur = con.cursor()

    cur.execute('SELECT * FROM pg_catalog.pg_tables')
    rows = cur.fetchall()
    print(rows)

    cur.execute("SELECT * from mlflow_clope")

    return cur.fetchall()


def get_clusters(tr, clust):
    cl = []
    new = []
    for i in range(len(clust)):
        cl = []
        for transact_ind in tr:
            cluster = tr[transact_ind]
            if cluster == i:
                cl.append(' '.join(trasactions[transact_ind]))
        new.append(cl)

    cl = []
    cl1 = []
    for i in range(0, len(clust)):
        for name in range(len(new[i])):
            cl.append(new[i][name])
            cl1.append(i)

    clope_data = pd.DataFrame(cl, columns=['name'])
    clope_data['clusters_count'] = pd.Series(cl1)
    clope_data = clope_data.sort_values(by='name')

    return clope_data


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


if __name__ == "__main__":

    data = pd.DataFrame(data=db_connection(), columns=['ind', 'items.name', 'items.price', 'items.quantity' ])
    data = data.iloc[:, 1:]

    print(data)
    # data = pd.read_csv('clustering_clope/data - data kika.csv', delimiter=';',
    #                    names=['items.name', 'items.price', 'items.quantity'])

    name = data.drop(['items.price', 'items.quantity'], axis=1)

    nmp = name['items.name'].to_numpy()

    i = 0
    list_of_sentance = []
    for sentance in nmp:
        list_of_sentance.append(sentance.split())

    trasactions = {i: transact for i, transact in enumerate(np.transpose(list_of_sentance))}

    print("Running example.py")

    parser = argparse.ArgumentParser()
    parser.add_argument("--noiseLimit")
    parser.add_argument("--seed")
    parser.add_argument("--r")
    args = parser.parse_args()

    noiseLimit = int(args.noiseLimit)
    seed = int(args.seed)
    r = float(args.r)

    mlflow.set_tracking_uri("http://mlflow:5000")
    mlflow.set_experiment('clustering')

    with mlflow.start_run():
        if not os.path.exists("outputs"):
            os.makedirs("outputs")
        data.to_csv('outputs/data.csv')

        log_param("noiseLimit", noiseLimit)
        log_param("seed", seed)
        log_param("r ", r)

        print("Train model")
        clope = CLOPE(print_step=100, is_save_history=True, random_seed=seed)
        clope.init_clusters(trasactions, r, noiseLimit)
        clope.print_history_count(r, seed)
        print("Clusters count %s" % len(clope))
        log_metric("clope clustering_clope", len(clope))
        print("Model saved in run %s" % active_run().info.run_uuid)
        print("Success")

        new_data = get_clusters(clope.transaction, clope)
        data = data.sort_values(by='items.name')
        new_data['price'] = data['items.price']
        new_data['quantity'] = data['items.quantity']
        print(new_data)

        new_data.to_csv('outputs/data_markup.csv')
        log_artifacts('outputs')

        mlflow.sklearn.log_model(sk_model=clope, artifact_path="output", registered_model_name='clope')

        engine = create_engine("postgresql://db:123456@postgres:5432/db")
        sql = 'DROP TABLE IF EXISTS data_markup;'
        engine.execute(sql)
        new_data.to_sql('data_markup', engine, method=psql_insert_copy)
        print('---------------')
