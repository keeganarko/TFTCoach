---
type: reference
scope: set-bound
set: 18
fetched: 2026-08-12
source: researched from named pro sources (attributed per section)
---

# Set 18 Enchanted Wilds — preview and launch doctrine

Future-prep, not current-game context: excluded from Set 17 coaching prompts, becomes primary meta knowledge on Aug 26 while stats are blacked out.

---
type: reference
scope: set-bound
set: 18
status: pre-launch (written 2026-08-11 from PBE coverage)
---

# Set 18 "Enchanted Wilds" — launch facts

- **Live: Wednesday Aug 26 2026, patch 18.1** (Liquipedia Patch_TFT18.1 lists 2026-08-26; Riot's official overview says Aug 26; one outlet says Aug 25 — treat Aug 26 NA as canonical). Set 17 "Space Gods" ends the same day. Full meta reset; ranked reset with the set.
- **PBE ran Jul 28 → launch, an extended 4-week window** because of the engine migration — PBE reads are better-tested than a normal set, but balance still shifted daily.
- **First set on Unreal Engine** (off Hextech, shared with LoL since 2019). Riot: same game, new internals. CONSEQUENCES: (1) the HUD is re-rendered — every pixel region and OCR assumption must be re-verified on day 1; (2) small bugs expected at launch — a weird interaction may be a bug, not a mechanic; (3) a **dedicated standalone PC client ships ~October 2026** — capture target changes again then; (4) cosmetics migrate gradually, with a rarity-tier "borrow" trial system.
- Scale: **65 champions** (14×1-cost, 13×2-cost, 14×3-cost, 14×4-cost, 10×5-cost), **~36 traits** (13 origins, 12 classes, ~10 one-unit traits + hidden Eclipse), **250+ new augments**, **~163 Wisp effects** in PBE data.
- Returning systems per PBE coverage: carousel, encounters.
- BOUNDARY: everything numeric in this note came from PBE; 18.1 launch patch notes supersede all of it. Re-verify shop odds, XP costs, and pool sizes from the official 18.1 notes on Aug 26 — they were NOT published as of Aug 11.

---

---
type: reference
scope: set-bound
set: 18
---

# Wisps (Set 18 core mechanic)

Reimagined Charms (Set 12). Single-use purchasable powers sold through the shop.

## Rules (Riot official + PBE sites)
- A Wisp appears in the **rightmost shop slot in every other shop** (alternating planning phases). **Max 1 purchase per round** (exception: Blossom 9 allows 2).
- **Planning phase only.** If not bought, the Wisp fades at end of planning and **reveals the ordinary champion hidden behind it** — that unit remains purchasable during combat. Skipping a Wisp costs you nothing except the effect.
- **Cost scales from 0 gold to 45+** as the game progresses; power scales with price.
- **7 color-coded categories**: Champion, Combat, Gold/XP, Item, Misc, Risky, Shop.
- **From Stage 5 on, every other Wisp offered is guaranteed a Combat Wisp** — late game reliably offers raw fight power.
- Trait-gated Wisps exist (e.g. a Riftbeast-only Wisp appears only with the trait active). ~163 distinct effects in PBE data.
- Example effects: Grandmaster (Champion): gain a random 2-star 5-cost. Quicken (Combat): +25% AS for 3s. Lost Travelers (Champion): 3 gold of random champions.
- **Blossom trait is the Wisp vertical**: champions gain AD/AP/HP after each Wisp interaction; (3) Wisps upgraded, (5) Wisp in every shop, (7) gold back after Wisp purchases, (9) buy 2/round, (11) overflow.

## Coaching triggers (Keegan-specific)
- HIS #1 MEASURED LEAK: dies averaging 5.42 place with 30+ gold banked. Wisps are the designed sink for exactly that gold. HARD TRIGGER: **Stage 5+, HP below ~40, gold ≥ 30 → buy the Combat Wisp that round.** It is the only late-game way to convert banked gold directly into fight power without hitting shops.
- CONDITION: below 50 gold before Stage 4, only buy a Wisp if it advances your line (Champion/Item category for your comp, or you are Blossom) — BOUNDARY: don't break an interest threshold for a Misc/Shop Wisp early.
- CONDITION: Risky-category Wisps are gambles — BOUNDARY: never while HP-critical (<30 HP) or when top-4 is the goal.
- Wisp-or-not is a NEW per-round decision the coach must surface: every other planning phase, the rightmost slot is not a unit.

---

---
type: reference
scope: set-bound
set: 18
status: PBE snapshot 2026-08-11 — memberships/breakpoints shifted daily on PBE; regenerate from CommunityDragon via `python3 -m tftcoach.reference` on Aug 26
---

# Set 18 trait web + cost table

## Champions by cost (65 total)
- **1-cost (14):** Akali, Camille, Cinderling, Karma, Kobuko, Leona, Ornn, Pebbles, Rakan, Rek'Sai, Varus, Veigar, Xayah, Yorick
- **2-cost (13):** Alistar, Caitlyn, Elise, Gromp, Kayle, LeBlanc, Murkwolf, Scuttlecrab, Sejuani, Shen, Teemo, Warwick, Yunara
- **3-cost (14):** Azir, Cassiopeia, Diana, Fiddlesticks, Hecarim, Kha'Zix, Kog'Maw, Krug, Mama Beak, Master Yi, Rammus, Rengar, Tristana, Vi
- **4-cost (14):** Ahri, Amumu, Ancient Sentinel, Aphelios, Brambleback, Ezreal, Lillia, Malphite, Morgana, Nidalee, Sett, Sivir, Soraka, Zyra
- **5-cost (10):** Alune, Ashe, Draven, The Elder Dragon, Gnar, Ivern, Kennen, Lux (9 Avatar variants), Maokai, Taric
- First-ever playable jungle monsters: Cinderling, Pebbles, Gromp, Murkwolf, Scuttlecrab, Krug, Mama Beak (raptor), Ancient Sentinel, Brambleback, Elder Dragon.

## Origins (13)
- **Blossom** 3/5/7/9/11 — Wisp vertical (see Wisps note). Karma, Yorick, Yunara, Master Yi, Ahri, Sett, Ashe (+Lux).
- **Blackthorn** 2/4/6 — ally on the Blackthorn hex is **sacrificed at combat start**, granting team HP; Blackthorns gain stats scaled by the sacrifice's role/star/cost; (6) sacrifice survives with bonus stats. Rek'Sai, Veigar, Warwick, Azir, Malphite (+Lux). [Early PBE name "Eldritch" — Riot official uses Blackthorn.]
- **Coven** 3/4/5/7 — gather Essence from kills AND losses, convert at chosen reward thresholds; the set's loss-streak econ trait. Camille, Caitlyn, Elise, Cassiopeia, Morgana (+Lux).
- **Elderwood** 3/5/7/9/11 — placeable plants (Stonebark Tree, Lifebloom, Deepwood Protector) that gain HP/AP per Elderwood star level; positioning puzzle; plants reach 3-star at (11). Ornn, Xayah, Alistar, LeBlanc, Hecarim, Ezreal, Gnar (+Lux).
- **Fae** 2/4 — team damage/heal/shield attracts Pixies; each Pixie grants Fae AD/AP; (4) Golden Pixies grant gold after 7. Rakan, Xayah, Tristana, Lillia (+Lux).
- **Inferno** 2/3/5/7 — Burn+Wound; stacks with other Burns; (3+) shop-ignite rolls champions up a tier in ignited slots. Akali, Varus, Shen, Amumu, Kennen (+Lux).
- **Lunar** 2-5 — Lunar + adjacent allies gain AS/AP. Diana, Aphelios, Alune (+Lux).
- **Solar** 3 — team max-HP shield + bonus magic damage; scales per unique 3-star champion (partial true-damage conversion; 3-stars can ascend to 4-star in combat). Leona, Kayle, Sejuani (+Lux). Wants a reroll board.
- **ECLIPSE (hidden trait)** — activating BOTH Solar and Lunar unlocks Eclipse: periodically executes the lowest-HP enemy on a repeating timer. Not shown in the normal trait list.
- **Primal** 2/4 — choose 1 of 4 Primal Blessings per breakpoint. Vi, Nidalee, Sivir (+Lux).
- **Riftbeast** 3/5/7/10 — jungle-monster vertical. (3) gain an **Alpha Mark**: place on any Riftbeast for a unique per-unit ability upgrade (color-coded buff per beast, e.g. Cinderling Scarlet = AD per cast). (5) shops periodically **fill with Riftbeasts** after combat — upgrades while leveling. (7) growth pulses every 5s. (10) increased team size. **Elder Dragon: 2 board slots, counts +2 Riftbeast, AoE autos, board-wide stun/ignite, execute with Alpha Mark.**
- **Rival** 1/2 — Kha'Zix, Rengar; strongest Rival collects takedowns (3 for killing the other Rival); (2) both fieldable.
- **Sprykin** 3/5/7 — gain the Big Furry Friend (BFF); drop a Sprykin on it to choose its Rider; BFF ability changes melee vs ranged rider; (5/7) share % of BFF ability to team/Sprykins. Kobuko, Veigar, Teemo, Rammus, Tristana, Gnar.
- **Flora Fatalis** 1/2 — harvest on takedown (mana; (2) heal lowest ally). Fiddlesticks, Soraka.

## Classes (12)
Adaptor 2/3/4 (ability + stat flips on AD-vs-AP, whichever higher: Akali, Gromp, Kog'Maw, Master Yi, Nidalee) · Brawler 2/4/6 (team %HP) · Defender 2/4/6 (team Armor/MR) · Executioner 2/3/4 (crit + bleed true damage) · Hunter 2-5 (AD; Damage Amp for not swapping targets) · Invoker 2-5 (team mana regen) · Juggernaut 2/4/6 (team Durability) · Rapidfire 2-5 (team AS; Rapidfires stack AS per attack) · Ravager 2/4/6 (omnivamp + bonus damage, doubled vs low-HP) · Spellweaver 2-6 (team AP; AP per cast) · Summoner 2/3 (empowers summons: Yorick/Azir/Mama Beak/Zyra) · Vanguard 2/4/6 (max-HP shield at start and at HP threshold).

## One-unit traits
- **Avatar (Lux, 5-cost)** — 9 variants (Blossom, Blackthorn, Coven, Elderwood, Fae, Inferno, Lunar, Primal, Solar). Her origin **counts twice (+2)**; laser gains a per-origin effect. Holding an Avatar transforms other Avatars in YOUR shop to your variant; opponents can't see which variant you bought; sell to re-find other origins. This is the set's flex capstone — nearly any board levels into its Lux.
- **Apex Predator** (Elder Dragon) · **Attuned** (Alune: moon phases alternate team Durability/Damage Amp per cast) · **Bounty Seeker** (Draven: choose bounty objectives → escalating rewards) · **Caustic** (Kog'Maw: shred+sunder) · **Emerald Aspect** (Taric: pair an ally to Taric for large bonuses) · **Greenfather** (Ivern: seeds grow biome hexes — Tree/Rock/Water/Flower/Mushroom buffs) · **Monolith** (Malphite: Armor/MR per enemy targeting him) · **Old Growth** (Maokai: permanent max HP per nearby enemy death) · **Thornmaiden** (Zyra: team Durability, more while plants alive).

BOUNDARY: trait memberships and breakpoints above are the PBE snapshot — trust the web's SHAPE, verify numbers against the auto-generated CommunityDragon reference note after Aug 26.

---

---
type: meta
scope: patch-bound
set: 18
status: PBE-derived theorycraft, 2026-08-11. Comp NAMES will be wrong by 18.1; the ARCHETYPES usually survive. Replace with live data as soon as Meta/Current Patch.md repopulates (~Aug 28-29).
---

# Set 18 launch archetypes (loose)

1. **Fae Xayah reroll (1-cost reroll)** — Xayah flagged "completely busted" on early PBE: armor shred on ability + passive AS ramp with Fae pixies. Guinsoo's Rageblade / Giant Slayer / Red Buff; Rakan + Shen frontline (Steadfast Heart/Bramble/Redemption). Stable at level 7; slow-roll for 3-stars if uncontested, else push 8. BOUNDARY: the single most likely target of the first B-patch — if 18.1b nerfs her, the shell (Fae + Rapidfire AS carry) likely persists.
2. **Riftbeast vertical (fast 9/10)** — buy every Riftbeast tag; (3) place the Alpha Mark on the current carry; (5) shop-overrun finds upgrades WHILE leveling — this trait pays you to push levels; capstone Elder Dragon (2 slots, +2 trait). Directly attacks Keegan's never-hits-9 leak: the trait subsidizes the level push.
3. **Elderwood control** — plant units stall combat; pairs with the Solar+Lunar hidden **Eclipse** execute for stall-then-execute boards.
4. **Blossom Wisp-econ** — buy Wisps early and often; (7) refunds gold, (9) doubles purchases; out-scales lobbies that ignore the mechanic. The designed "greedy econ" line of the set.
5. **Solar 3-star reroll** — Solar explicitly scales per unique 3-star champion (ascension to 4-star): Leona/Kayle/Sejuani reroll shell.
6. **Coven loss-streak opener** — essence from losses makes Coven the sanctioned open-fort line; convert essence at the right threshold, not the first one.
7. **Avatar Lux flex** — any strong board levels to 9 and caps with the Lux variant matching its origin (+2). The set's universal flex capstone.
8. **2-cost reroll (unnamed on PBE)** — slow-roll at 6 above 50g for a 2-cost core; IE/LW/HoJ style AD items cited. Held loosest of all.

BOUNDARY on all of the above: PBE tier lists were explicitly "guessing" (memuplay's own words) and S-tier Monday was B-tier Friday. Trust: archetype existence HIGH, unit names MEDIUM, item builds LOW, tier ordering NONE.

---

---
type: reference
scope: set-bound
set: 18
---

# What survives the Aug 26 reset — and what dies

## HOLDS (keep trusting these vault notes)
- **Economy**: interest breakpoints (10/20/30/40/50), streak gold, the value of 50g — "economy is the one system that did not reset, so it is your fastest edge on day one."
- **Rolldown STRUCTURE**: the math of when/why to roll (Game Math.md) — the framework holds even though the odds TABLE must be re-verified for Set 18.
- **Stage rhythm**: carousel and PvE rounds return; augments at the usual cadence (verify 2-1/3-2/4-2 in 18.1 notes); encounters return.
- **Positioning/scouting fundamentals** (Strategy Rules.md): corner carries, clump-vs-spread, scouting before planning ends — unit-agnostic, all valid.
- **Item component recipes**: no recipe rework announced; completed-item behavior carries. Artifact/radiant POOLS change contents.
- **Tempo doctrine**: strongest-board, win-streak math, HP-as-resource.

## DIES AUG 26 (quarantine these)
- **Every Set 17 comp, unit, trait, augment read** — Space Gods content including all of High Elo Playbook.md's comp timings and hex maps, Comps/, Meta/Current Patch.md.
- **Set 17's set mechanic** and its decision rules.
- **Set 17 shop-odds and pool-size tables** — Set 18 has a different champion distribution (14/13/14/14/10); per-champion bag sizes and level odds are NOT confirmed to match.
- **Unit-specific positioning** (ranges/mana note is set-bound, regenerate).

## NEW SYSTEMS TO LEARN (no Set 17 analogue)
- Wisps (every-other-round purchase decision — see Wisps note).
- Alpha Mark placement (a new per-fight itemization-like choice for Riftbeast).
- Avatar Lux variant economics (which origin, when to sell to re-find).
- Blackthorn sacrifice hex (a positioning decision with a body cost).
- Hidden Eclipse activation (Solar+Lunar dual-vertical planning).

RULE: any coaching statement that names a Set 17 entity after Aug 26 is a bug, not advice.

---

---
type: strategy
scope: evergreen
note: consolidated from set-launch coverage and standard high-elo set-launch practice; principles recur every set
---

# How to climb during a set launch (week 1, any set)

1. **Week-1 tier lists are guesses.** No stats exist; PBE balance ≠ live balance; the first B-patch (historically ~day 3-4) deletes 1-2 overtuned lines. Forcing a "day-1 S-tier" comp is how you hold the bag after the hotfix. Use tier lists for DIRECTION (which archetypes exist), never for FORCING.
2. **Strongest-board tempo beats greed.** In a confused lobby, boards are weak and uncapped — play upgrades the shop actually gives you, streak early, and level aggressively. Week 1 is the EASIEST time to hit level 9 (relevant: Keegan's measured never-hits-9 leak) because nobody's board punishes you for it.
3. **2-1 augment = direction, not lock.** Commit at 3-2 once items + shop confirm a line. Nobody has a verified augment tier list — your own reads are worth real LP; paper-mediocre prismatics can be broken in an unsolved meta.
4. **Econ is the unchanged edge.** Interest breakpoints didn't reset. The single most repeated launch-week win condition: clean interest management punishing players who over-roll at level 7 chasing units they can't stabilize.
5. **Uncontested > optimal.** When the "best" comp is 3-way contested and nobody knows the true best anyway, the open line wins the lobby.
6. **Bank reps in normals first.** 2-3 normals (~30 min each) to learn Wisp categories, Alpha Marks, and Avatar Lux before queuing ranked — mechanic fluency compounds across every ranked game after. "Set launch is the only time the whole ladder is confused at once" — the player who learned the mechanic yesterday farms the ones learning it live.
7. **Watch line-discovery, not tier lists**: day-1 streams/VODs of top players (Dishsoap, k3soju, Setsuko, Frodan co-streams) show WHY lines work; the first credible site tier lists land ~day 2-3 and are already partially stale on arrival.
8. **Expect volatility**: 18.1 launch → 18.1b B-patch within ~week 1 is the historical pattern; re-check patch notes before every session in week 1.

BOUNDARY: this doctrine applies to weeks 1-2 of a set. Once real stats stabilize (Meta/Current Patch.md repopulating with 300+ game comps), data outranks doctrine.
