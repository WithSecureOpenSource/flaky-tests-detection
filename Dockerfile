FROM python:3.9-slim-buster

COPY setup.py /
COPY flaky_tests_detection /flaky_tests_detection
COPY entrypoint.sh /entrypoint.sh
COPY README.md /
COPY Makefile /Makefile

RUN apt update && apt -y install make
RUN make install

ENTRYPOINT ["/entrypoint.sh"]
