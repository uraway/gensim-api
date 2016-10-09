FROM python:2.7.9

RUN pip install --upgrade pip

WORKDIR /gensim-api
COPY requirements.txt /gensim-api
RUN  pip install -r requirements.txt
COPY . /gensim-api
