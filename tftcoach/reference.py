"""Generates vault/Reference/ notes from CommunityDragon.

Trait breakpoints and item recipes are what let the coach answer "do I gain a
breakpoint by adding this unit" and "what do these two components make" — the
questions a comp tier list cannot touch. Both are set-bound, so they are
regenerated rather than written by hand; Set 18 on Aug 26 just means re-running
this.

    python3 -m tftcoach.reference
"""

from __future__ import annotations

import datetime
import json
import os
import re
import urllib.request
from typing import Any, Dict, List, Optional, Tuple

try:
    from . import config
    from .meta_feed import clean_name
except ImportError:  # direct execution
    import config                       # type: ignore
    from meta_feed import clean_name    # type: ignore

CDRAGON_URL = config.CDRAGON_TFT_URL
UA = "Mozilla/5.0 (TFTCoach personal coaching tool)"

# Basic components — the ones that actually combine into completed items.
COMPONENT_HINT = (
    "BFSword", "RecurveBow", "NeedlesslyLargeRod", "TearOfTheGoddess",
    "ChainVest", "NegatronCloak", "GiantsBelt", "SparringGloves", "Spatula",
)


def _fetch(url: str, timeout: int = 120) -> Optional[Any]:
    req = urllib.request.Request(url, headers={"User-Agent": UA})
    try:
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            return json.loads(resp.read().decode("utf-8"))
    except Exception:
        return None


def _current_set(data: Dict[str, Any]) -> Tuple[str, Dict[str, Any]]:
    sets = data.get("sets") or {}
    numeric = [k for k in sets if str(k).isdigit()]
    if not numeric:
        return "?", {}
    latest = max(numeric, key=lambda k: int(k))
    return latest, sets[latest]


def trait_breakpoints(set_obj: Dict[str, Any]) -> List[Dict[str, Any]]:
    """[{name, breakpoints: [2,4,6], desc}] — the unit counts that matter."""
    out: List[Dict[str, Any]] = []
    for trait in (set_obj.get("traits") or []):
        if not isinstance(trait, dict):
            continue
        points: List[int] = []
        for eff in (trait.get("effects") or []):
            if not isinstance(eff, dict):
                continue
            mn = eff.get("minUnits")
            # maxUnits is a sentinel like 25000 for "and above"; ignore it.
            if isinstance(mn, (int, float)) and 1 <= mn <= 12:
                points.append(int(mn))
        points = sorted(set(points))
        if not points:
            continue
        desc = re.sub(r"<[^>]+>", "", str(trait.get("desc") or ""))
        desc = re.sub(r"\s+", " ", desc).strip()
        out.append({"name": trait.get("name") or clean_name(
            str(trait.get("apiName", ""))), "breakpoints": points,
            "desc": desc[:240]})
    out.sort(key=lambda t: t["name"])
    return out


def item_recipes(data: Dict[str, Any], set_prefix: str) -> List[Dict[str, Any]]:
    """[{item, components:[a,b]}] for 2-component combines only."""
    by_api = {}
    for item in (data.get("items") or []):
        if isinstance(item, dict) and item.get("apiName"):
            by_api[item["apiName"]] = item

    out: List[Dict[str, Any]] = []
    for item in by_api.values():
        comp = item.get("composition") or []
        if len(comp) != 2:
            continue
        api = str(item.get("apiName", ""))
        # Keep the shared core items plus this set's own; skip other sets'.
        if not (api.startswith("TFT_Item_") or api.startswith(set_prefix)):
            continue
        names = []
        for part in comp:
            src = by_api.get(part)
            names.append(clean_name(str(src.get("name") if src else part)))
        out.append({"item": clean_name(str(item.get("name") or api)),
                    "components": names})
    # Deduplicate by item name; some sets re-declare the same recipe.
    seen = set()
    unique = []
    for row in sorted(out, key=lambda r: r["item"]):
        if row["item"] in seen or not row["item"]:
            continue
        seen.add(row["item"])
        unique.append(row)
    return unique


def render(set_num: str, traits: List[Dict[str, Any]],
           recipes: List[Dict[str, Any]]) -> str:
    today = datetime.date.today().isoformat()
    lines = [
        "---",
        "type: reference",
        "scope: set-bound",
        "set: {0}".format(set_num),
        "fetched: {0}".format(today),
        "source: CommunityDragon",
        "generated_by: tftcoach.reference",
        "---",
        "",
        "# Set {0} trait breakpoints and item recipes".format(set_num),
        "",
        "Auto-generated {0}. Regenerate after a set change: "
        "`python3 -m tftcoach.reference`.".format(today),
        "",
        "## Trait breakpoints",
        "",
        "Adding a unit only matters if it crosses one of these numbers.",
        "",
    ]
    for trait in traits:
        lines.append("- **{0}**: {1}".format(
            trait["name"], "/".join(str(b) for b in trait["breakpoints"])))
    lines += ["", "## Item recipes", "",
              "Which two components combine into each completed item.", ""]
    for row in recipes:
        lines.append("- **{0}** = {1} + {2}".format(
            row["item"], row["components"][0], row["components"][1]))
    lines.append("")
    return "\n".join(lines)


def refresh(verbose: bool = True) -> Tuple[bool, str]:
    if verbose:
        print("Fetching CommunityDragon (~26 MB) ...")
    data = _fetch(CDRAGON_URL)
    if not isinstance(data, dict):
        return False, "could not fetch CommunityDragon"
    set_num, set_obj = _current_set(data)
    prefix = "TFT{0}_".format(set_num)
    traits = trait_breakpoints(set_obj)
    recipes = item_recipes(data, prefix)
    if not traits and not recipes:
        return False, "parsed CommunityDragon but found no traits or recipes"

    out_dir = os.path.join(config.VAULT_DIR, "Reference")
    os.makedirs(out_dir, exist_ok=True)
    path = os.path.join(out_dir, "Set Traits and Item Recipes.md")
    with open(path, "w", encoding="utf-8") as fh:
        fh.write(render(set_num, traits, recipes))
    msg = "Wrote {0} traits and {1} item recipes (set {2}) to {3}".format(
        len(traits), len(recipes), set_num, path)
    if verbose:
        print(msg)
    return True, msg


if __name__ == "__main__":
    ok, message = refresh()
    print(("OK: " if ok else "FAILED: ") + message)
