FROM python:3.9-slim-buster

COPY flaky_tests_detection entrypoint.sh /

RUN pip install -e .

ENTRYPOINT ["/entrypoint.sh"]
