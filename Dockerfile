FROM python:3.10 AS build

COPY src src
COPY pyproject.toml .
RUN pip wheel --wheel-dir wheels --no-deps .

FROM datopian/giftless:0.5.0

USER root
COPY --from=build wheels wheels
RUN pip install wheels/*.whl
USER giftless
ENTRYPOINT ["tini", "uwsgi", "--"]
CMD ["--socket", "0.0.0.0:5000", "--callable", "app"]
