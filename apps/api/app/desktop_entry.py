"""Entry point for the standalone Windows backend executable."""

import argparse
import os


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--port", type=int, default=8000)
    parser.add_argument("--snapshot-dir")
    parser.add_argument("--web-dir")
    args = parser.parse_args()
    from dotenv import load_dotenv

    load_dotenv(os.environ.get("URBANFLOW_ENV_FILE", ".env"))
    if args.snapshot_dir:
        os.environ["URBANFLOW_SNAPSHOT_DIR"] = args.snapshot_dir
        # Explicit desktop demo mode; never embeds shared database credentials.
        if not os.environ.get("URBANFLOW_MONGODB_URI"):
            os.environ["URBANFLOW_DATA_SOURCE"] = "snapshot"
    if args.web_dir:
        os.environ["URBANFLOW_WEB_DIR"] = args.web_dir
    import uvicorn

    from app.main import app

    uvicorn.run(app, host="127.0.0.1", port=args.port, log_level="warning")


if __name__ == "__main__":
    main()
