import os
from pathlib import Path

import uvicorn
from dotenv import load_dotenv


def _load_shared_env() -> None:
    current = Path(__file__).resolve()
    candidates = [current.parents[1] / ".env", current.parent / ".env"]
    env_file = next((path for path in candidates if path.exists()), candidates[-1])
    load_dotenv(env_file)


def main() -> None:
    _load_shared_env()
    host = os.getenv("ANI_COL_HOST", "0.0.0.0")
    port = int(os.getenv("ANI_COL_PORT", "8060"))
    reload = os.getenv("ANI_COL_RELOAD", "false").lower() in {"1", "true", "yes", "on"}

    uvicorn.run("app.main:app", host=host, port=port, reload=reload)


if __name__ == "__main__":
    main()
