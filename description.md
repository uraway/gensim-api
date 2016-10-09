# 単語をベクトル化するword2vec(gensim)を使い、指定した二単語間の関連度を算出する

## word2vec

2014年から2015年辺りに流行った、単語をベクトル化して評価する手法。
有名なのは、

    king – man + woman = queen

### 学習データとなるコーパスを準備する

無料かつ簡単に手に入るWikipediaのdumpファイルから持ってきます。

<https://dumps.wikimedia.org/jawiki/latest/> の
jawiki-latest-pages-articles.xml.bz2 をダウンロードします。

xmlファイルのままでは使えないので、
これを[wp2txt](https://github.com/yohasebe/wp2txt)を使ってplain.txtに変換します:

    $ gem install wp2txt
    $ wp2txt jawiki-latest-pages-articles.xml.bz2

ファイルが大量に作成されるので、次のように連結します:

    $ cat jawiki-latest-pages-articles.xml-* > jawiki.txt

word2vecでは、単語ごとにスペースで区切られている必要があるので、日本語形態素解析器であるMecabを使って分かち書きします。

まずは、Mecabと標準辞書(IPA)をインストールします:

    $ brew install mecab mecab-ipadic

さらに[mecab-ipadic-NEologd](https://github.com/neologd/mecab-ipadic-neologd/blob/master/README.ja.md)というカスタム辞書をインストールします:

    $ git clone --depth 1 https://github.com/neologd/mecab-ipadic-neologd.git
    $ cd mecab-ipadic-neologd
    $ ./bin/install-mecab-ipadic-neologd -n

Mecabと辞書のインストールが完了しました。まずはカスタム辞書のインストール先を調べます:

    $ echo `mecab-config --dicdir`"/mecab-ipadic-neologd"
    /usr/local/lib/mecab/dic/mecab-ipadic-neologd

Mecabの -d オプションにこのパスを指定して、分かち書きを行います:

    $ mecab -d /usr/local/lib/mecab/dic/mecab-ipadic-neologd \
    -Owakati jawiki.txt > jawiki_wakati.txt

これで学習データの準備が整いました。

### word2vecの実装

    参考
    - <https://radimrehurek.com/gensim/models/word2vec.html>
    - <http://rare-technologies.com/word2vec-tutorial/>
    - <http://tjo.hatenablog.com/entry/2014/06/19/233949>
    - <http://sucrose.hatenablog.com/entry/2013/10/29/001041>

Pythonのgensimを使って、word2vecを使用します。cythonを入れると学習時間が短縮されるみたいです。

    $ easy_install gensim numpy scipy
    $ pip install cython

まずは、学習のためのスクリプトを記述、実行します:

`train.py`

```python
# -*- coding: utf-8 -*-
from gensim.models import word2vec
import logging

logging.basicConfig(format='%(asctime)s : %(levelname)s : %(message)s', level=logging.INFO)

sentences = word2vec.Text8Corpus('jawiki_wakati.txt')

model = word2vec.Word2Vec(sentences, size=200, min_count=20, window=15)

model.save("jawiki_wakati.model")
```

    $ python train.py

あまりにも時間がかかりすぎる場合はファイルを分割します。最終的に100MBほどに分割して学習させました。

これでモデルができました。ちょっと動作を確かめてみましょう。

`similarity.py`

```python
# -*- coding: utf-8 -*-
from gensim.models import word2vec
import logging
import sys

logging.basicConfig(format='%(asctime)s : %(levelname)s : %(message)s', level=logging.INFO)

model = word2vec.Word2Vec.load("jawiki_wakati.model")
argvs = sys.argv
print model.similarity(argvs[1], argvs[2])
```

これを実行します。

    $ python similarity.py 日本 フィリピン
    2016-09-09 21:57:52,064 : INFO : loading Word2Vec object from jawiki_wakati.model
    2016-09-09 21:58:03,569 : INFO : loading syn0 from jawiki_wakati.model.syn0.npy with mmap=None
    2016-09-09 21:58:03,956 : INFO : loading syn1 from jawiki_wakati.model.syn1.npy with mmap=None
    2016-09-09 21:58:04,573 : INFO : setting ignored attribute syn0norm to None
    0.262511504266

学習量が少ないので正確性にはかけるのでしょうが、ちゃんと単語類似度を返しています。

### APIとして使う

ほかのプログラミング言語から使用しやすいように、APIとして使えるようにしてみます。

フレームワークには[Falcon](https://falconframework.org/)を使用、WSGIサーバーのgunicornも一緒にインストールします。

    $ pip install falcon gunicorn

簡単に、2つのトークンを受け取って、類似度をJSONで返すAPIを作成します:

`server.py`
```python
# -*- coding:utf-8 -*-
import json
import falcon
from gensim.models import word2vec
import logging

class Server(object):

    def __init__(self):
        self.logger = logging.basicConfig(format='%(asctime)s : %(levelname)s : %(message)s', level=logging.INFO)
        self.model = word2vec.Word2Vec.load("jawiki_wakati.model")

    def on_get(self, req, res):

        s1 = req.get_param('s1')
        s2 = req.get_param('s2')

        content = {
            "similarity": self.model.similarity(s1, s2)
        }

        res.body = json.dumps(content)

app = falcon.API()
app.add_route("/", Server())
```

サーバーを動かしてみます:

    $ gunicorn server:app

次のようにGETリクエストを送ると、JSONで返ってきます:

    $ curl "127.0.0.1:8000?s1=日本&s2=フィリピン"
    {"similarity": 0.26251150426566316}

### Docker

デプロイしやすいようにDockerで動かしてみます。

現在の環境はこれ:
![](http://i.imgur.com/PcqxvKz.png)

Dockerファイルを追加:

`Dockerfile`
```
FROM python:2.7.9

RUN pip install --upgrade pip

WORKDIR /gensim-api
COPY requirements.txt /gensim-api
RUN  pip install -r requirements.txt
COPY . /gensim-api
```

管理が楽なのでDocker Composeを使用:

`docker-compose.yml`
```
api:
    image: gensim-api
    command: gunicorn --reload -b 0.0.0.0:5000 server:app
    volumes:
        - .:/gensim-api
    ports:
        - "5000:5000"
```

次のコマンドでDockerイメージを作成し、コンテナを起動します:
```
docker build -t gensim-api .
docker-compose up
```

### 最後に

上記のように、gensimを使えば簡単に単語の類似度が算出できることが分かりました。学習データの準備さえ乗り越えれば、あとはどうってことないと思います。

ソースコードはこちら:

<https://github.com/uraway/gensim-api>

今のところ、学習量は100MBなんですが、続けて学習させることも可能っぽいので、適度に更新しておきます。

単語の類似度以外にもいろいろ出来そうです。
