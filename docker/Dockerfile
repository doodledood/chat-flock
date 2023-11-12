FROM python:3.8.1-slim-buster

ENV LANG=C.UTF-8 \
  LC_ALL=C.UTF-8 \
  PATH="${PATH}:/root/.poetry/bin"

RUN apt-get update && \
  apt-get install -y --no-install-recommends \
  curl \
  && rm -rf /var/lib/apt/lists/*

COPY pyproject.toml ./

# Add PyPI as a trusted host in pip.conf
RUN pip config set global.trusted-host files.pythonhosted.org

# Install Poetry
RUN curl -sSL https://install.python-poetry.org | POETRY_HOME=/opt/poetry python
RUN cd /usr/local/bin && \
    ln -s /opt/poetry/bin/poetry && \
    poetry config virtualenvs.create false

# Ignore SSL errors when installing dependencies
RUN poetry config repositories.FPHO https://files.pythonhosted.org
RUN poetry config certificates.FPHO.cert false

# Allow installing dev dependencies to run tests
ARG INSTALL_DEV=false
RUN bash -c "if [ $INSTALL_DEV == 'true' ] ; then poetry install --no-root ; else poetry install --no-root --only main; fi"

CMD mkdir -p /workspace
WORKDIR /workspace
