FROM python:alpine

CMD ["flask", "run", "--host", "0.0.0.0"]
EXPOSE 5000
ENV FLASK_APP="thsapi/__init__.py" \
    FLASK_ENV="development"

COPY . /app
WORKDIR /app
RUN pip install .
