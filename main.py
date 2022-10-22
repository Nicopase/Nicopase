from flask import Flask, request, send_file
from flask_restful import Api, Resource
import base64
import requests
import cv2
import numpy as np
import uuid
import psycopg2

app = Flask(__name__)
api = Api(app)

collages = dict()

client_id = "195f7bdba7564b82b45f4d83a1c2b40c"
client_secret = "0896e2223216411a99d98a6957a1833b"
id_secret = f"{client_id}:{client_secret}"

encodedBytes = base64.b64encode(id_secret.encode("utf-8"))
encodedStr = str(encodedBytes, "utf-8")

header = {'Authorization': f'Basic {encodedStr}',
          'Content-type': 'application/x-www-form-urlencoded'}

connection = psycopg2.connect(
        user = "postgres",
        password = "1234",
        host = "localhost",
        port = "5432",
        database = "demo"
    )
cursor = connection.cursor()
cursor.execute("SELECT version();")


# @app.route('/token')
def get_token():
    response = requests.post(url="https://accounts.spotify.com/api/token", data={'grant_type': 'client_credentials'},
                             headers=header)
    token_response = response.json()
    print(token_response)
    return token_response


# @app.route("/test")
def test():
    return "hello"


# @app.route('/test2')
def get_image(album_name):
    token = get_token()["access_token"]
    head = {'Authorization': f'Bearer {token}',
            'Content-type': 'application/json',
            'Accept': 'application/json', }
    payload = {'q': album_name, 'type': 'album'}
    response = requests.get(url="https://api.spotify.com/v1/search", params=payload,
                            headers=head)
    image_url = response.json()["albums"]["items"][0]["images"][1]["url"]
    return image_url


def make_collage(cover_list):
    img1 = cv2.imread(f'{cover_list[0]}.jpeg')
    img2 = cv2.imread(f'{cover_list[1]}.jpeg')
    im_h = cv2.hconcat([img1, img2])

    img3 = cv2.imread(f'{cover_list[2]}.jpeg')
    img4 = cv2.imread(f'{cover_list[3]}.jpeg')
    im_h2 = cv2.hconcat([img3, img4])

    collage = cv2.vconcat([im_h, im_h2])

    filename = str(uuid.uuid4())
    cv2.imwrite(f'{filename}.jpeg', collage)
    return filename


# @app.route('/images')
def get_images(album_list):
    album_urls = []
    for album in album_list:
        album_urls.append(get_image(album))
    for i in range(len(album_list)):
        img_data = requests.get(album_urls[i]).content
        with open(f'{album_list[i]}.jpeg', 'wb') as handler:
            handler.write(img_data)


@app.route('/collage')
def get_collage():
    arr_list = request.args.getlist("album")
    get_images(arr_list)
    filename = make_collage(arr_list)
    # collages[filename] = arr_list
    cursor.execute("SELECT version();")
    return {'link': f'http://127.0.0.1:5000/share/{filename}'}


@app.route("/download/<file>")
def download_image(file):
    return send_file(f'{file}.jpeg', mimetype='image/jpeg')


@app.route("/share/<file>")
def share_collage(file):
    cursor.execute("SELECT version();")
    return {'link': f'http://127.0.0.1:5000/download/{file}',
            'albums': collages[file]}


if __name__ == "__main__":
    app.run(debug=True)
