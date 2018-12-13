FROM python:alpine

ARG couchdb_user
ARG couchdb_pass

CMD ["flask", "run", "--host", "0.0.0.0"]
EXPOSE 5000
ENV FLASK_APP="thsapi" \
    FLASK_ENV="production"

COPY . /app
WORKDIR /app
RUN pip install .
RUN flask init-db $couchdb_user $couchdb_pass
