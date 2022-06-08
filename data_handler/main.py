import boto3
import psycopg2
from fastapi import FastAPI, File, UploadFile
import uvicorn
from pydantic import BaseModel

app = FastAPI()


class Data(BaseModel):
    data: str


def db_connection():
    con = psycopg2.connect(
        database="db",
        user="db",
        password="123456",
        host="postgres",
        port="5432"
    )

    cur = con.cursor()
    cur.execute("CREATE TABLE IF NOT EXISTS new_data (id serial PRIMARY KEY, data varchar);")
    con.commit()
    return con
    # return cur.fetchall()


@app.get("/new_data")
async def read_data():
    return {"Hello": "World"}


@app.post('/set_data/')
async def set_data(data: Data):
    text = data.data
    cur = connection.cursor()
    cur.execute('INSERT INTO new_data (data) VALUES '
                f"('{text}');")
    connection.commit()


# @app.post("/uploadfile/")
# async def create_upload_file(file: bytes = File(...)):
#     s3 = boto3.resource('s3',
#                         endpoint_url='http://minio:9000',
#                         config=boto3.session.Config(signature_version='s3v4')
#                         )
#
#     s3.Bucket('test-bucket').upload_file('/home/', 'piano.mp3')
#
#     return {"filename": file.filename}

connection = db_connection()

if __name__ == '__main__':
    uvicorn.run(app, port=8000, host='0.0.0.0')
