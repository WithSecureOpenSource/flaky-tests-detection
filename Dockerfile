FROM python:3.9-slim-buster

COPY setup.py /setup.py
COPY flaky_tests_detection /flaky_tests_detection
COPY flaky_tests_detection/check_flakes.py /check_flakes.py
COPY entrypoint.sh /entrypoint.sh
COPY README.md /README.md

RUN pip install -e .

ENTRYPOINT ["/entrypoint.sh"]
