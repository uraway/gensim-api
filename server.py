# -*- coding:utf-8 -*-
import json
import falcon
from gensim.models import word2vec
import logging
import os, sys

class Server(object):

    def __init__(self):
        self.logger = logging.basicConfig(format='%(asctime)s : %(levelname)s : %(message)s', level=logging.INFO)
        self.model = word2vec.Word2Vec.load("./models/jawiki_wakati.model")

    def on_get(self, req, res):
        s = req.get_param('s')
        s1 = req.get_param('s1')
        s2 = req.get_param('s2')

        if s1 and s2:
            try:
                sim = self.model.similarity(s1, s2)
            except:
                sim = 0

            content = {
                "similarity": sim
            }
            res.body = json.dumps(content)

        else:
            try:
                result = self.model.most_similar(positive = s, negative = [], topn = 3)
            except:
                result = []

            for i in result:
                print i[0]

            res.body = json.dumps(result)


app = falcon.API()
app.add_route("/", Server())
