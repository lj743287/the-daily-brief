import json
import os
from pathlib import Path

BASE_DIR = Path(".")
DATA_DIR = BASE_DIR / "data"
STORIES_DIR = BASE_DIR / "stories"
FEATURES_DIR = BASE_DIR / "features"

MODE = os.getenv("REFRESH_MODE", "everything").strip().lower()


def delete_file(path: Path) -> None:
    if path.exists() and path.is_file():
        path.unlink()
        print(f"Deleted file: {path}")


def delete_generated_html(folder: Path) -> None:
    if not folder.exists():
        return
    for path in folder.glob("*.html"):
        if path.name == ".gitkeep":
            continue
        path.unlink()
        print(f"Deleted generated HTML: {path}")


def cleanup_news() -> None:
    delete_file(DATA_DIR / "stories.json")
    delete_generated_html(STORIES_DIR)


def cleanup_feature() -> None:
    feature_json = DATA_DIR / "feature.json"

    if feature_json.exists():
        try:
            with open(feature_json, "r", encoding="utf-8") as f:
                data = json.load(f)
            feature_url = data.get("url", "").strip()
            if feature_url:
                feature_path = BASE_DIR / feature_url
                delete_file(feature_path)
        except Exception as exc:
            print(f"Warning: could not read feature.json before cleanup: {exc}")

    delete_file(feature_json)


def main() -> None:
    print(f"Reset mode: {MODE}")

    if MODE == "news":
        cleanup_news()
    elif MODE == "features":
        cleanup_feature()
    elif MODE == "everything":
        cleanup_news()
        cleanup_feature()
    else:
        raise ValueError("REFRESH_MODE must be one of: news, features, everything")


if __name__ == "__main__":
    main()
