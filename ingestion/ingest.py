import os

import dlt
from dotenv import load_dotenv
from dlt.sources.credentials import ConnectionStringCredentials
from dlt.sources.sql_database import sql_database
from sqlalchemy.engine import URL

load_dotenv()


def create_source():
    password = os.getenv("SQL_SERVER_PASSWORD")
    if not password:
        raise ValueError(
            "SQL_SERVER_PASSWORD has not been configured in the .env file!"
        )

    connection_url = URL.create(
        "mssql+pyodbc",
        username=os.getenv("SQL_SERVER_USER", "maiypbn4"),
        password=password,
        host=os.getenv("SQL_SERVER_HOST", "45.124.94.158"),
        port=int(os.getenv("SQL_SERVER_PORT", "1433")),
        database=os.getenv("SQL_SERVER_DATABASE", "xomdata_dataset"),
        query={
            "driver": os.getenv(
                "SQL_SERVER_ODBC_DRIVER", "ODBC Driver 18 for SQL Server"
            ),
            "TrustServerCertificate": "yes",
        },
    )

    credentials = ConnectionStringCredentials(
        connection_url.render_as_string(hide_password=False)
    )
    return sql_database(
        credentials,
        schema="e_commerce",
        table_names=["customer", "ecom_sales", "product", "region"],
    )


def main():
    print("Trying to connect SQL Server ...")

    source = create_source()
    pipeline = dlt.pipeline(
        pipeline_name="xomdata_sqlserver_ingest",
        destination=dlt.destinations.duckdb("medallion.duckdb"),
        dataset_name="bronze",
    )
    info = pipeline.run(source, write_disposition="replace")

    print("Data has been loaded successfully!")
    print(info)


if __name__ == "__main__":
    main()
