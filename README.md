# gensim API

## Dependencies

- [gensim](https://radimrehurek.com/gensim/index.html)
- [falcon](https://falconframework.org/)

## Setup Server

    $ gunicorn server:app

## API

### Similarity

#### Request

##### route

    GET ?s1=[word]&s2=[word]

#### Response

##### body

    {"similarity": 0.26251150426566316}
