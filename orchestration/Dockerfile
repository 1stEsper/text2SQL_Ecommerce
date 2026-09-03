FROM apache/airflow:3.3.1-python3.13

USER root

# dlt connects to the source through Microsoft ODBC Driver 18 for SQL Server.
RUN apt-get update \
    && ACCEPT_EULA=Y apt-get install -y --no-install-recommends \
        msodbcsql18 \
        unixodbc-dev \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

USER airflow

COPY requirements.txt /tmp/orchestration-requirements.txt

# Requiring the image's Airflow version prevents pip from silently replacing it.
RUN pip install --no-cache-dir \
    "apache-airflow==${AIRFLOW_VERSION}" \
    -r /tmp/orchestration-requirements.txt
