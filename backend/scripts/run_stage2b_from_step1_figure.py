import asyncio
import json
from pathlib import Path
from typing import List, Dict, Any
import sys

# Ensure backend root is on sys.path
CURRENT_FILE = Path(__file__).resolve()
BACKEND_ROOT = CURRENT_FILE.parents[1]
if str(BACKEND_ROOT) not in sys.path:
    sys.path.insert(0, str(BACKEND_ROOT))

from app.services.schema_utils import get_multi_stage_extractor
from app.services.theta_client import ThetaClient
from app.services.extract import save_llm_debug_output
from app.core.config import settings


STEP1_DIR = Path("/Users/lorenzpiazolo/Documents/Theta Hackathon 25/_Code/Auralis/backend/exports/extraction/Step1")


def load_stage1_items() -> List[Dict[str, Any]]:
    """Load Stage 1 Figure outputs and build products_items list."""
    if not STEP1_DIR.exists():
        raise FileNotFoundError(f"Stage1 directory not found: {STEP1_DIR}")

    files = sorted(STEP1_DIR.glob("Figure_*_stage1.json"))
    products_items: List[Dict[str, Any]] = []

    for fp in files:
        try:
            data = json.loads(fp.read_text(encoding="utf-8"))
            llm = data.get("llm_response", {})
            products = llm.get("products", {})
            source = llm.get("source", {})
            if isinstance(products, dict) and products:
                products_items.append({
                    "products": products,
                    "source": source
                })
        except Exception:
            # Skip file if unreadable or malformed
            continue

    return products_items


async def run_stage2b(products_items: List[Dict[str, Any]]) -> Dict[str, Any]:
    extractor = get_multi_stage_extractor()
    prompt = extractor.build_stage2b_products_prompt(
        company_id="temp_comp_figure",
        products_items=products_items
    )

    client = ThetaClient(db_session=None)  # cache disabled; DB not used
    try:
        response = await client.complete(
            prompt=prompt,
            schema_version=settings.SCHEMA_VERSION,
            page_type="product_consolidation",
            competitor="Figure",
            session_id="manual_test",
            use_cache=False
        )
    finally:
        await client.close()

    # Save debug output alongside other exports
    save_llm_debug_output(
        stage="2B",
        url=f"consolidated_products_{len(products_items)}_pages",
        competitor="Figure",
        prompt=prompt,
        response=response,
        session_id="manual_test"
    )

    return response


async def main() -> None:
    items = load_stage1_items()
    print(f"Loaded Stage1 files with products: {len(items)}")
    if not items:
        print("No Stage1 product items found. Aborting.")
        return

    resp = await run_stage2b(items)
    products = resp.get("products", {}) if isinstance(resp, dict) else {}
    print(f"Stage2B products keys: {list(products.keys())[:10]}")
    print(f"Total products: {len(products)}")


if __name__ == "__main__":
    asyncio.run(main())
