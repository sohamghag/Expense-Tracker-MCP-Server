from pathlib import Path
import json
BASE_DIR = Path(__file__).resolve().parent.parent.parent
print(BASE_DIR)
CATEGORY_PATH = BASE_DIR / "categories.json"
print(CATEGORY_PATH)


with open(CATEGORY_PATH, "r", encoding="utf-8") as f:
    categories = json.load(f)

print(categories)