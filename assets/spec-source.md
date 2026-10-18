## 7. 3D rendering spec: "SEED Flagship Campus" (for Codex)
**Goal:** a 3D model of one ~83 MW SEED campus, the Cambridge, Massachusetts flagship, in architectural-visualization quality.
- **Main deliverable:** an interactive virtual tour that shows the technology, with labels saying what we chose, why, and how it works ("Virtual tour" below).
- **Also:** still renders S1–S4 from the same model.
- **Massing:** get it right from the dimensions below.
- **Tools:** the builder picks them. For example, model in Blender and export glTF to a three.js web viewer for the tour.

**Coordinates:**
- Meters. The origin is the center of the main hall's footprint at ground level; +x is east, +y is north, +z is up.
- The parcel runs x −350..300, y −330..200. The built area is gently rolling, nearly flat ground.
- The parcel sits at the urban edge of Cambridge: low industrial buildings, rail lines and street trees around it, with the Boston skyline on the southeastern horizon. The real parcel is still to be found; draw the campus as specified.

**Elements:**
1. **Main hall**
   - **Footprint:** x −105..105, y −30..30 (210 × 60 m).
   - **Roof:** a low single slope falling to the south, z = 8 m at y = −30 and z = 9.5 m at y = +30 (about 1.5°).
     - This keeps the hall below the cooler tops (~9.9 m) so the coolers breathe freely.
     - Standing seam #B9BCBF, with south-tilted solar panels (10°) on racks over about 85% of it (cells #1B2430, frames #C0C4C8), and a 2 m clear edge with snow guards.
   - **Walls:** insulated metal panels with a stone-wool core, in light warm gray #C9C6BF.
     - South and west faces: a vertical wood-look noncombustible rainscreen (e.g. wood-grain aluminum or fiber cement, #B07A45) up to 8 m.
     - North face: charcoal #3A3D40, with exposed aluminum-jacketed pipe risers (#D9D9D9).
   - **Openings:** no windows into the data halls. A 4 m south corridor (y −30..−26) has a narrow strip of windows 2–3 m above the ground. The east face has 3 loading-dock doors (4 × 4.5 m).
   - **Interior (for the cutaway only):**
     - Along x, 4 pods at x −95..−50, −50..−5, −5..40 and 40..85. Each pod is a data hall (its first 25 m) followed by an electrical room (the next 20 m).
     - The west end (−105..−95) holds network entry and fire protection. The east end (85..105) holds the loading dock and staging.
       - *Added 10/18 late evening (punch list 1k):* each of the 3 dock doors opens into a vestibule about 6 m deep with a second roll-up door, so the outer and inner doors are never open together.
       - New racks rest in the staging area for a few hours to warm up before they enter a hall.
     - Along y: corridor at −30..−26; halls and electrical rooms at −26..16; a north service spine (cooling distribution units, pumps, risers) at 16..30.
     - Each hall has 8 rows running north–south, alternating compute and networking:
       - 4 compute rows of 25 Vera Rubin NVL72 positions (100 per hall, 400 per site). 92 are powered at 190 kW (368 per site); the other 8 per hall are spare.
       - 4 rows of 23 networking and storage racks (~14 kW each), one for every compute rack.
       - Racks are 0.6 × 1.2 × 2.3 m (the same MGX frame as GB300). Compute racks are black with a blue LED strip; networking racks are dark gray.
     - The compute racks are fully liquid-cooled: cold plates inside, with hoses to manifolds at the back of each rack.
     - **Pipes below, power above** (*changed 10/18 late evening:* FM Global's 2026 data-center rules bar cooling pipes above racks; §5, "Fire protection and leak detection"):
       - **Below:** along each row, from the service spine, a covered trench in the floor slab under the aisle (about 0.9 m wide × 0.6 m deep, steel grating lids #6B7075). It carries welded stainless pipes (warm #D85A30 bands, cool #378ADD bands) over a drip liner with a leak-sensing rope. Short hoses rise to each rack's manifold.
       - **Above:** only the power busway and cable trays, plus sprinkler pipes and thin smoke-sampling pipes at the ceiling. Nothing carrying cooling water runs over a rack.
     - The networking and storage racks carry rear-door coils: a water coil on the rack's back door, pushed by the equipment's own fans. There are no hot-aisle chimneys or ceiling coils.
     - The cooling units (CDUs) stand at the north end of each row, in the service spine along the hall's edge, so no cooling unit or pipe joint sits over a rack.
     - Ceiling about 7 m clear.
     - **Condensation control** (*added 10/18 late evening;* handoff §5, "Condensation control"; punch list 1k). Small details, visible in X-ray:
       - **Dew point sensors:** two small white wall boxes (~0.15 m) per hall, about 1.8 m up. The hall air is kept drier than a 50°F (10°C) dew point, and the cooling units keep the water at least ~27°F warmer than that.
       - **Fresh-air unit:** one box about 6 × 2.5 × 2.5 m (illustrative size) in the service spine near the east end (around x 70..80, y 18..28). It draws outside air through a louvered opening in the north wall. A cold coil inside dries the air, with a thin drain line from it.
       - **Drain-down tanks** (freeze protection, punch list 1l): 2 horizontal tanks about 3 m across × 12 m long (illustrative size) in the service spine's west part (around x −95..−80, y 18..28), with 4 small upright expansion tanks beside them. Drain lines from the coolers come back over the pipe bridges and fall to these tanks.
2. **Cooling ridge**
   - **Deck:** an elevated steel deck at x −105..105, y 36..60, with its top at z = 6 m. Columns on a 6 m grid; galvanized grating #A7ADB2; guardrails; stairs at both ends.
   - **Dry coolers:** 102 modules in 6 rows along x, 17 per row. Each module is 12 × 2.4 × 2.6 m, with casing #E6E8EA and 8 black fans 1.0 m across on top. Each sits on ~1.3 m steel legs above the grating, so drifting snow stays clear of it (tops at ~9.9 m). The modules look identical; about 73 serve the warm chip loop and 29 the cooler room-air loop.
   - **No vapor plumes:** dry coolers use no water.
   - **Pipe bridges:** 3 bridges at x = −60, 0 and 60, spanning y 30..36 at about z = 7 m. Each is 4 m wide and carries 4 insulated pipes: 2 for the chip loop (0.6 m across) and 2 for the room-air loop (0.4 m across).
   - **Freeze protection** (*added 10/18 late evening;* handoff §5, "Freeze protection"; punch list 1l):
     - **Bypass valve station:** at the middle pipe bridge (x = 0), on the deck's south edge. A small platform about 4 × 3 m with a short pipe linking the warm and cool chip-loop headers, and a large motorized mixing valve (actuator safety yellow #E8B53A). In cold weather it sends some warm water around the coolers, so the building's water never drops below 70°F (21°C).
     - **At every cooler:** a shut-off valve with a small actuator on each of its two pipe connections, a drain valve at its lowest point, and a freeze sensor on its outlet. Small details, visible close up.
     - **Drain lines:** thin insulated lines run from the coolers' drain valves back along the pipe bridges to the drain-down tanks in the service spine (element 1).
     - **Optional, not drawn by default:** electric heat-tracing cable on exposed pipes, and wind screens on the deck.
   - **Backup chillers:** 6 warm-water air-cooled chillers of ~1.7 MW each (about 12 × 2.3 × 2.5 m each, casing #E6E8EA with large fans on top, like the coolers), long sides north–south in 3 columns of 2 with ~4 m between columns, on a concrete pad at grade at x 108..138, y 34..62, east of the deck, piped to the service spine. (*Changed 10/18 late evening* from 4 of ~2.5 MW, a size no maker in these lines offers.)
3. **Cold battery**
   - **Boreholes:** about 1,000 on a 5 m grid (32 × 32) across x −80..75, y −220..−65, nearest the Cold Battery House. They serve the room-air loop. The rest of the meadow stays open.
   - **Meadow:** a native meadow (#8FA35B in summer, #C8A55A in autumn) still covers x −200..200, y −310..−60, except where the gravel snow storage pad (element 9, x 120..200, y −120..−70) is cut out of its east side.
   - **Solar meadow:** about 2–3 MW of ground-mounted panels in east–west rows over the meadow, including the drilled field.
     - Tilted 25° to the south, front edge ~1 m above the meadow, rows ~6 m apart.
     - 4 m grass access lanes along the header lines and to each vault lid.
   - **At the surface:** optional flush lids 0.3 m across (very subtle), plus 2 header vaults with 3 × 3 m concrete lids at y ≈ −62.
   - **Cold Battery House:** x −15..15, y −55..−40, 6 m tall, timber-clad, with a green roof.
     - *Added 10/18 late evening (punch list 1k):* the cold pipes inside the house and running underground to the header vaults wear thick white insulation with a sealed jacket. In winter this loop runs as cold as about 19°F (−7°C). The buried runs show in ground cutaway.
   - **Cutaway:** soil from 0 to 1 m, glacial till from 1 to 15 m, bedrock below. Boreholes appear as thin U-shaped loops down to 150 m.
4. **Substation**
   - **Yard:** a gravel yard at x 140..210, y −40..40.
   - **Equipment:** 3 transformers (8 × 6 × 7 m), a control building (20 × 10 × 5 m) and steel gantries.
   - **Power line:** a 115 kV overhead line arrives from the east on lattice towers.
5. **Backup generator yard**
   - **Fence:** a fenced yard at x 150..270, y 70..170.
   - **Generators:** 30 containerized generator sets of ~3 MW (12.2 × 2.44 × 2.9 m, light gray #D0D3D6, each with a short exhaust stack) in 5 rows of 6: ~80 MW at full build plus a spare.
   - **Fuel:** 4 horizontal double-walled renewable-diesel tanks (about 3.5 m across × 29 m long, ~275 m³ each, ~1.1 million litres in all: 48 hours at full build) inside a low concrete spill wall at the east end.
   - **Reserved:** a marked gravel pad at the north end for future hydrogen fuel cells.
6. **SEED House (operations building)**
   - **Footprint:** x −185..−135, y −10..15.
   - **Form:** 2 stories (9 m) with exposed glulam and cross-laminated timber #D9B38C, floor-to-ceiling glass on the south and west, and a sedum roof #6E8B3D.
   - **Entrance:** a plaza on the west side with a low "SEED" sign.
7. **Waste-heat greenhouse**
   - **Footprint:** x −185..−125, y −50..−20.
   - **Form:** a glass gable roof with an 8 m ridge, white frame and lush plants inside.
   - **Heating:** warmed by the datacenter's return water.
8. **Parking**
   - **Area:** x −320..−210, y −60..40.
   - **Canopies:** 4 rows of solar canopies, each 100 × 12 m, with panels tilted 10° to the south and 3 m of clearance.
   - **Spaces:** about 200 cars.
9. **Roads and landscape**
   - **Roads:** an entry road from the southwest to the plaza, and a service loop around the hall to the dock and energy yard.
   - **Landscape:** fieldstone walls (#8C8577) along the entry road, and planted drainage swales.
   - **Snow storage:** a gravel pad at x 120..200, y −120..−70, cut out of the meadow (no grass under it). It sits just east of the borehole field and its solar rows (which end at x 115).
   - **Security:** a black mesh fence (2.4 m) around the operational zone (hall, deck, chiller pad, substation, generator yard), with trees for screening.

**Shots** (at least 1920×1080; 4K preferred):
- **S1, Hero:** aerial from the southwest, camera at about (−450, −450, 250) aimed at (0, 0, 0). Autumn, golden-hour sun from the southwest.
- **S2, Winter:** drone from the northeast, camera at about (350, 300, 60) aimed at (0, 30, 10). Snow on the ground, the meadow, the solar rows and the low roof; the cooler deck clear; the generator yard in the foreground.
- **S3, Cutaway:** a north–south section through pod 2's data hall (x ≈ −37) showing:
  - Liquid-cooled racks with their hoses rising from the covered floor trench, and a networking rack with its rear-door coil; power busway overhead
  - The chip loop running from the racks to the service spine, over the nearest pipe bridge to the cooling ridge, and back
  - The room-air loop running from the rear-door coils to the Cold Battery House and down the boreholes, with a branch to the backup chillers
  - Blue arrows for cool flow and red for warm
- **S4, Site plan:** top-down orthographic view with labels.

**Labels** (on S3/S4, or toggleable):
- "Sealed data halls: 368 Vera Rubin NVL72 racks, ~26,500 GPUs"
- "Warm-water chip cooling: up to 113°F (45°C) at the racks, no chillers for the chips"
- "Antifreeze loops: Dow's DOWFROST, never colder than the high teens °F"
- "Rear-door coils: the last 7–10% of heat, from networking gear"
- "Cooling ridge: 102 dry coolers, zero water"
- "Geothermal cooling: ~1,000 boreholes, 150 m deep, with 6 backup chillers"
- "Solar roof, canopies and meadow: ~5–6 MW"
- "Backup: batteries + renewable-diesel generators, ~80 MW, 48 hours of fuel"
- "Pipes below, power above: no water over the racks"
- "Freeze protection: a warm-water bypass, freeze sensors, and coolers that drain in a winter outage"
- "Dry halls: air drier than a 50°F (10°C) dew point; water never below 77°F (25°C) at the racks"
- "Grid connection: ~83 MW (1/6 of the 500 MW fleet)"
- "SEED House + waste-heat greenhouse"

**Virtual tour** (the main deliverable):
- **Format:** an interactive 3D web page (e.g. three.js loading a glTF model) that runs in a browser on a laptop and can be shared as a link.
- **Navigation:**
  - Back and Next through numbered stops, with a smooth camera flight between them.
  - A clickable list of stops.
  - Free orbit and zoom at any stop.
- **At each stop:**
  - Highlight the featured objects; dim the rest slightly.
  - Show the stop's **bubble** (below): the cue card the presenter reads from.
  - A **More** button on the bubble opens the stop's three-part card, **What we chose**, **Why**, **How it works** ("Card text for each stop" below), and a **Show the math** link to the matching section of the SEED math appendix: https://claude.ai/artifact/8ofePKB934K361bVkuPRN4
    - Anchors by stop: 1 #carbon, 2 #solar, 3 #racks, 4 and 5 #chip-loop, 6 #room-air, 7 #greenhouse, 8 #grid, 9 #backup, 10 #users; closing cards #budget and #baseline.
    - The page is private until Arturo shares it.
  - Use all text as written; don't add claims. The numbers are design estimates with sources in the appendix.
- **Toggles:**
  - **X-ray:** hide the main hall's roof and walls to see inside.
  - **Ground cutaway:** a section through the borehole field showing soil (0–1 m), glacial till (1–15 m), bedrock, and U-shaped loops down to 150 m.
  - **Heat flow:** animated pipes, warm water in red #D85A30 and cool in blue #378ADD.
    - The chip loop: racks → service spine → pipe bridges → coolers → back.
    - The room-air loop: rear-door coils → Cold Battery House → boreholes, and to the backup chillers on the hottest days.
    - A warm branch to the greenhouse.
  - **Season:**
    - Summer: green meadow; the ground takes heat.
    - Winter: snow; the coolers chill the ground again until it's colder than 14°F (−10°C) outside. Most coolers stand still and a few turn slowly. The bypass valve glows warm as some water skips the coolers.
  - **Labels:** on or off.

**Presentation: a hybrid storyboard (Arturo, 10/18 evening).** One mode, never switched:
- **The story drives.** Next and Back (arrow keys, Page Up / Page Down, or a presentation clicker) fly the camera to each stop, dim everything but the featured objects, and show that stop's bubble about half a second after the camera lands.
- **Bubbles are cue cards a presenter can read off the screen:** a headline of at most ~8 words that states the point; at most 3 bullets of ~10 words each; one big number with its unit; a small "We assume…" line whenever the number rests on an assumption; and a tiny source tag (e.g. "calc 09"). Pin each bubble beside its object with a thin leader line, and keep it readable on a projector (~40 px headline, ~24 px bullets at 1080p).
- **Explore without leaving the story:** at any stop, drag to orbit and zoom, or click any object for its explainer (below). The bubble tucks into a corner, and Next glides the camera back to the stop's view and carries on.
- **Plain language (Arturo, 10/18 evening):** all on-screen text (bubbles, explainers, labels) must make sense to someone who has never seen a datacenter.
  - No unexplained acronyms: "renewable diesel" not "HVO", "cooling units" not "CDUs", "about 90% of our power reaches the chips" not "PUE 1.1", "measured speed tests" not "MLPerf".
  - Everyday words and plain units. Any comparison used for scale must be sourced.
  - The test: could a non-expert read the bubble in about 5 seconds and get the point?
- **Every number on screen has a source** (Arturo, 10/18 late evening: "Everything we assert needs to have a reference and that reference needs to be verified"). Each bubble's tag points to the appendix calc that shows it; the references page lists every source and its check.

**Bubble text (plain language, checked against the sources 10/18 late evening).** Each bubble has a headline, up to 3 bullets, one big number, a "We assume…" line where the number rests on an assumption, and a source tag. Show them exactly as written.

| Card | Headline | Bullets | Big number | We assume… | Source tag |
|---|---|---|---|---|---|
| Opening (before stop 1) | SEED: AI datacenters that waste less power | • 500 MW of grid power, $30B, five years • Goal: serve 400 million knowledge workers • First campus: Cambridge, Massachusetts | **400 million** people served | — | Challenge slides |
| 1. SEED House | We rate the work, not the building | • Score: people served per megawatt of power • Plus the carbon and water each person costs • Wood where people work; steel where computers run | **800,000** people per megawatt | — | Challenge slides; calc 18 |
| 2. Solar | Sun on every roof cuts what we buy | • Panels on roofs, parking shades and the meadow • Inside our 500 MW limit: no extra computers • Small but real, and every bit helps | **~1%** of the site's power | …panels average ~14% of their rated output, the Massachusetts norm | calc 14 · US energy data (EIA) |
| 3. Inside a data hall | Water, not air, cools the chips | • 368 racks per site, about 26,500 AI chips • Each rack makes ~5× the heat air can carry • Sealed rooms: muggy, salty outside air stays out | **~200 kW** per rack | …~190–230 kW per rack, from trade reports; NVIDIA hasn't published it | calc 02 · NVIDIA |
| 4. Service spine | Warm water is cool enough | • The racks accept water up to 113°F (45°C) • So our water floats with the weather: 70–106°F (21–41°C) • Warm water can be cooled by plain outdoor air | **113°F (45°C)** warmest water the racks take | — | calc 07 · NVIDIA |
| 5. Cooling ridge | Outdoor air does the cooling, no water used | • 102 giant radiators with fans, on a raised deck • Sealed coils: no water evaporates, no cooling towers • No chillers needed for the chips | **8,759 of 8,760** hours a year | …a typical weather year; a hot summer needs ~20 hours of help | calc 09 · Boston weather file |
| 6. Geothermal cooling | Room air: the ground first, then chillers | • About 1,000 holes, 150 m (500 ft) deep • Winter air chills the rock; summer heat goes back in • Six air-cooled chillers stand by for heat waves | **30–40%** less energy than chillers alone | …the rock behaves like typical local granite; a test bore confirms it before drilling | calc 09 · our model |
| 7. Greenhouse | Waste heat warms a greenhouse | • Warm water leaving the halls heats the glass house • It needs well under 1 MW of our ~75 MW of heat • Heat is a resource, not just waste | **~124°F (51°C)** water, all year | …~300 W per m² of peak heating, a rough figure | calc 13 · our estimate |
| 8. Substation and grid | Clean power, under a firm cap | • Each site connects about 83 MW; six make 500 • We contract with new clean power plants • Massachusetts now asks big datacenters to do this | **500 MW** ≈ 9% of all electricity sold in Massachusetts, for scale | …we pay for the full 500 MW all five years | calc 15 · EIA 2024 · Executive Order 658 |
| 9. Backup power | Proven backup, on cleaner fuel | • Batteries carry the first minutes, cooling pumps included • Then ~30 generators run on renewable diesel • 48 hours of fuel on site; deliveries after that | **50–80%** less carbon over the fuel's life | …certified waste-oil fuel; soy-based fuel saves less (~47%) | calc 16 · Kao Data · California fuel data |
| 10. The whole campus | More of every watt reaches the chips | • About 90% of our power reaches the computers • A typical large datacenter: about 70% • Fast AI models by default serve all 400 million | **31%** more chips on the same 500 MW | …most everyday work runs on fast AI models | calc 01 · Uptime Institute 2025 |
| Closing 1: what it costs | All 400 million served, inside the budget | • Vera Rubin racks from day one • Fast models by default, bigger ones when needed • About $13–14B of the $30B left unspent | **$15.8–17.2B** of $30B | …mid price estimates; rack prices are analyst estimates | calc 17 · budget model |
| Closing 2: against a typical datacenter | Costs a bit more to build, much less to run | • Build: about $0.2B more than a typical design • Electricity: about $90 million a year less • Water: almost none; cooling towers would use ~4.5 billion litres a year | **~2.5 years** to pay back the extra | …power at 14¢ per kWh, racks running full time | calc 20 · Uptime 2025 · LBNL |

- **The big number** is the largest text on the bubble, with its unit underneath.
- **Temperatures are in °F first, with °C in brackets** (Arturo, 10/18 late evening), in all on-screen text: bubbles, explainers, cards and labels.
- **The cooling fluid is named:** Dow's DOWFROST. On screen it's always described cautiously, as "never colder than the high teens °F; stays liquid down to about 2°F" (Arturo: "in the teens to be safe").
- **Plain-language checks done on this text:**
  - No acronyms. "MW" and "kW" are spelled as written because the challenge uses them; the explainers spell them out once ("megawatts").
  - Every comparison has a source: "~5× the heat air can carry" uses NVIDIA's ~40 kW limit for air-cooled racks against ~200 kW; "about 70%" is 1 ÷ 1.44 from the Uptime Institute's 2025 survey.
- **Presenter's script:** the speaking notes (§10) follow these bubbles stop by stop, adding only what the screen doesn't say.

**Click anything (Arturo, 10/18 evening): every object below is clickable.**
- **Interaction:** an object highlights on hover. A click opens an explainer panel with the object's name, two or three short sentences, one key number, and two links:
  - "Show the math": the SEED math appendix, https://claude.ai/artifact/8ofePKB934K361bVkuPRN4 plus the anchor given.
  - "Why we chose it": the SEED Basis of Design, https://claude.ai/artifact/65FXnUpGEvJaqCACavodDt plus the anchor given.
- **Text:** use it as written and don't add claims. Close the panel with Esc or a click elsewhere. In X-ray mode, the hall's inside objects become clickable.

| Object (element in this spec) | Explainer (plain language) | Key number | Math | Why |
|---|---|---|---|---|
| Main hall (1) | A one-story steel hall with stone-wool walls that can't burn, as insurers require. The low roof keeps the coolers' tops above it, so they breathe freely. | 210 × 60 m, roof 8–9.5 m | #snow | #hall |
| Roof solar (1) | Panels on the hall roof. They count inside our 500 megawatt (MW) limit, so they cut the power we buy rather than adding computers. | ~2.2 MW of panels | #solar | #power |
| Sealed data hall (1, X-ray) | Outside air never comes in. Boston-area air has the right humidity for computers only 69% of the year, so we cool through water instead. | 4 halls per site | #humidity | #sealed |
| Compute rack (1, X-ray) | An NVIDIA Vera Rubin rack: 72 AI chips (GPUs), cooled by water through metal plates on every chip. Water goes in at up to 113°F (45°C) and comes out at about 131°F (55°C). | 368 per site, ~26,500 chips | #racks | #computers |
| Networking and storage rack with rear-door coil (1, X-ray) | It holds the network switches and the flash drives that remember each user's conversations. Its own fans push warm air through a water coil on its back door, so the heat goes straight to water. | 14 kW per rack | #room-air | #room-air |
| Floor pipe trench (1, X-ray) | Cooling pipes run in covered trenches in the floor, never over the racks, as insurers now require. A leak drains into a lined trench with a sensing cable, and power cables run overhead, away from water. | no pipe joints above any rack | — | #fire |
| Sprinklers and smoke sampling (1, X-ray) | Wet-pipe sprinklers: always full of water, the safest choice for people. Thin pipes draw air to very sensitive smoke detectors, so alarms sound before smoke builds. | ~500 gallons a minute where a fire starts | — | #fire |
| Service spine and cooling units (1) | Cooling units at the end of each row pass the racks' heat to the building's water. That water floats between 70 and 106°F (21–41°C) with the weather. | returns at ~124°F (51°C) | #chip-loop | #chip-loop |
| Electrical rooms and batteries (1, X-ray) | Batteries carry the computers *and* the cooling pumps until the generators start. If the pumps stopped, the chip water would warm about 4°F (2.4°C) a minute. | generators take over in ~10 seconds | #stoppage | #backup |
| Pipe bridges (2) | They carry the warm chip loop and the cooler room-air loop between the hall and the cooling ridge. Outside the halls, the loops carry Dow's DOWFROST antifreeze. | 3 bridges, 4 pipes each | #chip-loop | #chip-loop |
| Dry coolers (2) | Giant radiators with fans. Outdoor air cools the chip loop through sealed coils, so nothing evaporates, and the chips never need chillers in a typical year. The fluid is water mixed with Dow's DOWFROST antifreeze: in normal running it never gets colder than the high teens °F, and it stays liquid down to about 2°F (−16°C). | 8,759 of 8,760 hours | #chip-loop | #chip-loop |
| Backup chillers (2) | Air conditioners for water. Six stand by to cool the room-air water in heat waves or when the borehole field is serviced. They use no water. | 6 units, 10 MW in all | #room-air | #room-air |
| Borehole field (3, ground cutaway) | About 1,000 holes, 500 ft (150 m) deep. Winter air chills the rock; on warm days the rock takes the room air's heat with only pumps running. This is geothermal cooling, not power. | 30–40% less energy than chillers alone | #room-air | #room-air |
| Cold Battery House (3) | The pumps and pipes that run the borehole field. It's timber-clad, with a green roof. | covers ~2,290 warm hours a year | #room-air | #room-air |
| Meadow and parking-canopy solar (3, 8) | More panels over the meadow and the parking. With the roof they make about 1% of the site's power. | ~5.8 MW of panels per site | #solar | #power |
| Substation (4) | Where the site connects to the grid: about 83 MW from a 115,000-volt line. We buy clean power through contracts with new clean power plants. | 6 sites × ~83 MW = 500 MW | #grid | #power |
| Generator yard (5) | About 30 standard generators running on renewable diesel, made from fats and oils (we require waste sources). Cleaner engines keep smog-forming exhaust low. It isn't zero-emission, but it cuts the fuel's lifetime carbon by 50–80%. | ~3 MW each | #backup | #backup |
| Fuel tanks (5) | Two days (48 hours) of renewable diesel on site, with a delivery contract for longer outages. | ~1.1 million litres at full build | #backup | #backup |
| Reserved fuel-cell pad (5) | Space kept for hydrogen fuel cells once they're proven at this scale. Today they would cost far more. | +$0.70–0.78B if built now | #backup | #backup |
| SEED House (6) | The operations building, and the one place we use mass timber, which stores carbon. | 2 stories, planted roof | #carbon | #house |
| Waste-heat greenhouse (7) | Warm water leaving the halls heats it on the way to the coolers. | needs under 1 MW of ~75 MW | #greenhouse | #house |
| Snow storage pad (9) | Plowed snow goes here, away from the coolers' air intakes and the wetlands. | design snow ~0.6 m deep | #snow | #hall |
| Dew point sensors (1, X-ray) | They measure how damp the hall air is. A surface warmer than the air's "dew point" stays dry, so we keep the dew point under 50°F (10°C) and the water at least ~27°F warmer. Nothing "sweats" like a cold glass on a summer day. | water never below 77°F (25°C) at the racks | #chip-loop | #sealed |
| Fresh-air unit (1, X-ray) | It brings in the small amount of fresh air staff need and keeps the halls at slightly higher pressure, so any leak blows dry air out instead of letting damp air in. A cold coil wrings the moisture out of that air first. | hall air drier than a 50°F (10°C) dew point | #humidity | #sealed |
| Loading-dock airlock and staging (1) | Two doors with a space between them, never open together, so damp or icy outdoor air stays out. New racks rest here for a few hours to warm up, so they don't fog up like a cold bottle brought indoors. | 3 dock doors, each with an airlock | — | #sealed |
| Bypass valve (2) | In cold weather, outdoor air could chill the water far too much. Like a car's thermostat, this valve sends some warm water around the coolers, so the building's water never drops below 70°F (21°C). | never below 70°F (21°C) | #chip-loop | #fluid |
| Cooler valves, drain lines and freeze sensors (2) | Each cooler has a freeze sensor and its own shut-off and drain valves. If a long winter power outage stops the heat, the coolers are closed off and drained into indoor tanks, while the pumps keep running on backup power. | pumps need under 1 MW of backup | #stoppage | #fluid |
| Drain-down tanks (1, X-ray) | Indoor tanks that catch the coolers' fluid in a winter outage. Any fluid left in a cooler turns to slush, not ice, so pipes and coils don't burst; it thaws before cooling restarts. | all 102 coolers drain here | #stoppage | #fluid |
| Insulated cold pipes (3, ground cutaway) | In winter the ground loop runs as cold as about 19°F (−7°C). Its pipes wear thick insulation with a sealed jacket, so damp air can't reach the cold metal and drip. | as cold as ~19°F (−7°C) in winter | #room-air | #room-air |

| # | Stop | Camera at → looking at (m) | Toggles on |
|---|---|---|---|
| 1 | Arrival: SEED House | (−260, −60, 12) → (−160, 2, 5) | — |
| 2 | Solar | (−320, −380, 160) → (−60, −120, 0) | — |
| 3 | Inside a data hall | (−37, −22, 4) → (−37, 5, 1.5) | X-ray |
| 4 | Service spine | (−20, 10, 7) → (−37, 23, 2) | X-ray, heat flow |
| 5 | Cooling ridge | (70, 120, 35) → (0, 45, 7) | Heat flow |
| 6 | Geothermal cooling | (140, −230, 40) → (0, −120, −60) | Ground cutaway, heat flow, season |
| 7 | Greenhouse | (−235, −95, 10) → (−155, −35, 4) | Heat flow |
| 8 | Substation and grid | (265, −95, 30) → (175, 0, 5) | — |
| 9 | Backup power | (330, 60, 35) → (210, 120, 3) | — |
| 10 | The whole campus | (−450, −450, 250) → (0, 0, 0) | Heat flow |

**Card text for each stop** (opened by the bubble's **More** button):
1. **SEED House**
   - *What we chose:* a two-story mass-timber operations building (glulam and cross-laminated timber) with a green sedum roof.
   - *Why:* timber stores carbon and cuts embodied carbon where people work. Insurers want the data halls noncombustible, so the timber goes here.
   - *How it works:* the campus is run from here. SEED rates the work, not the building: users served per megawatt, and the carbon and water each user costs.
   - *Show the math:*
     - Users per megawatt: 400 million ÷ 500 MW = 800,000.
     - Embodied carbon: building and IT, each spread over its life, ≈ 30–66 kt CO2e a year; ÷ 400 million users ≈ 0.08–0.17 kg per user-year (estimate).
2. **Solar**
   - *What we chose:* about 3.3 MW of panels on the hall roof and parking canopies, plus about 2–3 MW over the borehole meadow.
   - *Why:* every bit helps. Everything stays inside the 500 MW cap, so solar doesn't add chips; it cuts the energy we buy from the grid, and with it cost and carbon.
   - *How it works:* in Massachusetts, panels average about 14% of their rated output (17% of their inverter rating, per US energy data), so this is roughly 1% of the site's power. The rest is clean power bought from the grid.
   - *Show the math:*
     - 3.3 MW of roof and canopy panels × ~14% + 2–3 MW of meadow (inverter rating) × 17% ≈ 0.8–1.0 MW, about 1% of the site's 83 MW, or ~7–9 GWh a year not bought from the grid.
     - Meadow: 260 × 250 m ≈ 16 acres, at about 5.5–7.6 acres per MW (NREL) ≈ 2–3 MW.
3. **Inside a sealed data hall**
   - *What we chose:* NVIDIA Vera Rubin NVL72 racks (72 GPUs each, 190–230 kW), fully liquid-cooled, in sealed, vapor-tight halls.
   - *Why:* air-cooled racks top out near 40 kW (NVIDIA's guidance), and these draw ~190–230 kW. Sealing keeps muggy summer air, dry winter air and salt outside.
   - *How it works:* cold plates on every chip pass the heat into water, which goes in at up to 113°F (45°C) and comes out at about 131°F (55°C). Networking racks get rear-door coils, pushed by their own fans. The water never drops below 77°F (25°C), well above the hall air's dew point (kept under 50°F, 10°C), so nothing condenses on the pipes or chips.
   - *Show the math:*
     - 75 MW for chips ÷ (190 kW per compute rack + 14 kW for its networking rack) ≈ 368 racks; × 72 GPUs ≈ 26,500 GPUs.
     - Water out: NVIDIA says coolant entering a Rubin chip at 113°F (45°C) leaves at about 131°F (55°C). Lenovo's flow table for the earlier GB300 rack gives ~131°F (55°C) out at every inlet from 77 to 113°F (25–45°C), so we assume the same for Rubin (our estimate).
4. **Service spine**
   - *What we chose:* cooling units and pumps along the hall's north side, one cooling unit at the end of each row, with pipes to the racks in covered floor trenches.
   - *Why:* it's one short run from every hall to the coolers, it keeps pipes out of the electrical rooms, and no cooling pipe runs over a rack, as insurers require.
   - *How it works:* the units pass heat from the rack loop to the building loop. That water floats between 70 and 106°F (21–41°C) with the weather and returns at about 124°F (51°C).
   - *Show the math:*
     - Rack inlet ≤ 113°F (45°C), minus ~7°F (4°C) across the cooling units, means building water ≤ 106°F (41°C).
     - Return: the racks' ~131°F (55°C) − 7°F ≈ 124°F (51°C).
5. **Cooling ridge**
   - *What we chose:* 102 dry coolers on short legs on a 6 m steel deck, fed by three pipe bridges. No cooling towers, and no chillers for the chips.
   - *Why:* dry coolers use no water, and warm-water chips let outdoor air do all the cooling in all but one hour of a typical year.
   - *How it works:* fans pull outside air up through finned coils. The fluid inside is water mixed with Dow's DOWFROST antifreeze (an inhibited propylene glycol), so in normal running it never gets colder than the high teens °F, and it stays liquid down to about 2°F (−16°C). About 73 coolers serve the chips and 29 the room air. The deck and legs keep snow clear. In winter the fans slow, coolers switch off, and a bypass valve keeps the building's water at 70°F (21°C) or warmer. In a long winter outage, the coolers are closed off and drained into indoor tanks.
   - *Show the math:*
     - Coolers bring water within ~9°F (5°C) of the outside air, so 106°F (41°C) water works up to 97°F (36°C) outdoors. Cambridge's hottest hour (Boston-Logan weather file, 2011–2025) is 97°F (36.1°C): 1 hour in 8,760.
     - Cooler fans use about 0.2% of the site's energy a year.
6. **Geothermal cooling**
   - *What we chose:* about 1,000 boreholes, 150 m deep under the meadow, run from the Cold Battery House, with six air-cooled chillers as backup.
   - *Why:* on warm days outdoor air can't make the 75°F (24°C) water the room-air loop needs. The ground does it with only pumps running, using less power than chillers every year; the chillers are insurance.
   - *How it works:* in winter the same coolers chill the rock; in summer heat goes back into it. This is geothermal cooling, not power: rock hot enough for power is 4–6 miles down here.
   - *Show the math:*
     - Room-air heat: networking racks (~14 kW per compute rack, 4.3–5.1 MW) + electrical losses (1–3% of 75 MW) ≈ 5–7 MW.
     - Coolers make 75°F (24°C) water only when it's below 66°F (19°C) outside. In Cambridge it's warmer than that ~2,290 hours a year, and the ground covers those hours.
     - An hour-by-hour model needs ~950 boreholes (~1,050 in a hot summer, with the chillers covering the gap), so we drill ~1,000.
     - Against chillers alone, the field saves ~650–1,130 MWh a year and 1.1–1.7 MW at the hottest hour per site (preliminary model outputs).
7. **Greenhouse**
   - *What we chose:* a glass greenhouse heated by the datacenter.
   - *Why:* it puts waste heat to use instead of sending it all into the air.
   - *How it works:* warm return water at about 124°F (51°C) runs through the greenhouse's heating loop on its way to the coolers.
   - *Show the math:* the return water carries all ~75 MW at about 124°F (51°C). The 60 × 30 m greenhouse needs well under 1 MW at peak (about 1,800 m² × ~300 W/m², rough), a sliver of what's available.
8. **Substation and grid**
   - *What we chose:* a ~83 MW grid connection (one-sixth of the 500 MW fleet), with clean power bought through contracts with new clean power plants.
   - *Why:* the challenge caps grid power. Massachusetts has no geothermal power plants and only modest sun, so clean power is bought, not made. The state's new rules for big datacenters (Executive Order 658, September 2026) ask for exactly this: new clean generation to match what we use.
   - *How it works:* a 115,000-volt line comes in from the east and transformers step it down.
   - *Show the math:*
     - 500 MW × 8,760 hours = 4.4 TWh a year, ~9% of the electricity sold in Massachusetts (49.4 TWh).
     - At 18.2¢/kWh that's ~$4B over 5 years; each 1¢/kWh is ~$220M.
9. **Backup power**
   - *What we chose:* batteries for the first minutes, then standard generators running on renewable diesel, with room to add hydrogen fuel cells later.
   - *Why:* it's proven and insurable, and Kao Data has run its UK campus this way since 2021. Renewable diesel cuts the generators' lifetime fuel carbon by 50–80%, and they only run for tests and rare outages, so backup fuel is under 1% of the site's footprint.
   - *How it works:* if the grid drops, batteries carry the load for minutes while about 30 generators start. 48 hours of fuel sits in four tanks, and deliveries keep them running in longer outages.
   - *Show the math:*
     - Fuel: 48 h × ~82 MW × ~0.28 L/kWh ≈ 1.1 million litres at full build; ~0.48–0.53 million for the first racks.
     - Kao Data's Harlow campus plans "more than 750,000 litres" of HVO for 35–71 MW of IT.
     - Carbon: 20 test hours a year ≈ 0.2 million litres ≈ 510–570 t CO₂ on diesel, ~100–290 t on renewable diesel, against ~86,000–97,000 t for a year of grid power at New England's 2024 mix.
10. **The whole campus**
    - *What we chose:* one of six ~83 MW SEED sites, together sized to serve case C: 400 million knowledge workers.
    - *Why:* under a 500 MW cap, every watt not spent on cooling serves users. About 90% of the power reaches the chips, against about 70% at a typical large datacenter.
    - *How it works:* fast AI models by default, larger ones when a task needs them. No water evaporated for cooling; backup generators run on renewable diesel only for tests and outages.
    - *Show the math:*
      - Total power ÷ computer power is the industry's "power usage effectiveness": 1.44 for typical large sites (Uptime Institute, 2025), 1.1 for SEED (a design allowance).
      - 500 MW ÷ 1.1 ≈ 455 MW to the chips, against 500 ÷ 1.44 ≈ 347 MW: 31% more.
      - Case C on a fast open model (gpt-oss-120b: 13,400–15,000 tokens/s per GB300 GPU in MLPerf v6.0, or 18,760–21,000 once the test's own prompt processing is taken out): 400 million users × (4.6 + 40 ÷ 10) tokens/s ÷ 18,760–21,000 ≈ 164,000–183,000 GB300 GPUs. ÷ Vera Rubin's 1.5–1.8× per watt ≈ 37–50% of the fleet's power.
      - Stress test, all on the heaviest measured model (Llama 3.1 405B, 617–646 tokens/s per GPU with prompt processing taken out): 5.3–5.6 million GB300 GPUs, 12–15× the fleet on Vera Rubin, so ~7–8% of users served. Fast models by default are what make 100% possible.

**Left to the builder:** textures, vegetation, people and cars, rack and pipe detail, lighting, and the choice of tool.

**Leave out:** cooling towers or vapor plumes, space hardware, and Amaru branding.

