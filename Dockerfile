FROM python:3.9-slim-buster

COPY setup.py /
COPY flaky_tests_detection /flaky_tests_detection
COPY entrypoint.sh /
COPY README.md /

RUN pip install -e .

ENTRYPOINT ["/entrypoint.sh"]
