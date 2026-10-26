"""CLI entrypoint; transformations remain inside the reusable package."""

from urbanflow_etl.ingestion.download import main

if __name__ == "__main__":
    main()
