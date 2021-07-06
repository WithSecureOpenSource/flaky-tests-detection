FROM python:3.9-slim-buster

COPY check_flakes.py entrypoint.sh requirements.txt /

RUN pip install -r requirements.txt

ENTRYPOINT ["/entrypoint.sh"]
