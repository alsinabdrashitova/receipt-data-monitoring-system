from __future__ import print_function
import os
import argparse
from sklearn.cluster import DBSCAN
from sklearn.preprocessing import StandardScaler
import mlflow
import pandas as pd
import numpy as np
import psycopg2
import csv
from sklearn.metrics.pairwise import cosine_similarity
from io import StringIO
import mlflow.sklearn
from sklearn.feature_extraction.text import TfidfVectorizer
from mlflow import log_metric, log_param, log_artifacts, active_run
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

    data = pd.DataFrame(data=db_connection())
    data = data.iloc[:, 1:]

    # nmp = data['items.name'].to_numpy()
    nmp = data.iloc[:, 6].to_numpy()

    model_vect = TfidfVectorizer()
    tf_idf_matrix = model_vect.fit_transform(nmp)
    dictionary = dict(zip(model_vect.get_feature_names(), list(model_vect.idf_)))
    dist = 1 - cosine_similarity(tf_idf_matrix)

    parser = argparse.ArgumentParser()
    parser.add_argument("--eps")
    parser.add_argument("--min_samples")
    args = parser.parse_args()

    eps = float(args.eps)
    min_samples = int(args.min_samples)

    mlflow.set_tracking_uri("http://mlflow:5000")
    mlflow.set_experiment('clustering_dbscan')

    with mlflow.start_run():
        if not os.path.exists("outputs"):
            os.makedirs("outputs")

        log_param("eps", eps)
        log_param("min_samples", min_samples)

        print("Train dbscan model")
        db_default = DBSCAN(eps=eps, min_samples=min_samples).fit(dist)
        labels = db_default.labels_
        lab, count = np.unique(labels[labels >= 0], return_counts=True)
        log_metric("dbscan", len(set(labels)))

        data['cluster'] = pd.Series(labels)

        data.to_excel('outputs/data_markup_dbscan.xlsx')
        log_artifacts('outputs')

        mlflow.sklearn.log_model(sk_model=db_default, artifact_path="output", registered_model_name='dbscan')
