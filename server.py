# -*- coding:utf-8 -*-
import json
import falcon
from gensim.models import word2vec
import logging
import os, sys
import boto
import boto.s3.connection

LOCAL_PATH='./models/'
AWS_ACCESS_ID=os.getenv('AWS_ACCESS_ID')
AWS_ACCESS_TOKEN=os.getenv('AWS_ACCESS_TOKEN')

class Server(object):

    def __init__(self):
        conn = boto.connect_s3(AWS_ACCESS_ID, AWS_ACCESS_TOKEN)
        bucket = conn.get_bucket('gensim-models')

        key = bucket.get_key('jawiki_wakati.model')
        key.get_contents_to_filename('./models/jawiki_wakati.model')

        self.logger = logging.basicConfig(format='%(asctime)s : %(levelname)s : %(message)s', level=logging.INFO)
        self.model = word2vec.Word2Vec.load("./models/jawiki_wakati.model")

    def on_get(self, req, res):

        s1 = req.get_param('s1')
        s2 = req.get_param('s2')

        content = {
            "similarity": self.model.similarity(s1, s2)
        }

        res.body = json.dumps(content)

app = falcon.API()
app.add_route("/", Server())
