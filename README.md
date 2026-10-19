# SEED Cambridge campus

An interactive, static 3D presentation built from the SEED handoff, with the user-approved top-model baseline applied on October 18, 2026. The editable Blender scene is the geometric source of truth; the browser loads its exported GLB.

## Run

From this folder:

```sh
npm start
```

Open http://localhost:4173 in Chrome. All model, code and presentation assets are local; the choice explanations, calculations supplied for each stop, and basis-of-design details are included inside the main card. Optional original-source links need an internet connection. A static server is required; opening index.html directly from Finder will not load the model.

No build or package download is needed for the supplied copy. To use another static server, serve this folder unchanged. Dependencies are pinned in package.json and package-lock.json, and Three.js is vendored.

## Public website

The public repository is `arturo-natella/seed-cambridge-tour`. Vercel builds the static website with `node scripts/build-site.mjs` and publishes `dist/`. This build uses Node's standard library, needs no environment variables, and does not require Blender or the original handoff documents.

Run `npm run build` to reproduce the published website. The output includes the interactive tour and Blender still gallery. The repository also includes the editable Blender master, authoring scripts and JSON verification reports. Local archives, Blender backup files, dependencies and QA screenshots are excluded from Git.

## Present

- Next / Back, arrow keys, Page Down / Page Up, or a clicker step through the opening, ten stops, and two closing cards.
- Tour stops jumps directly to a card. Home returns to the opening; End opens the final comparison.
- Drag to orbit; scroll or pinch to zoom. The cue card tucks away while exploring. Next returns to the story and advances.
- Each stop has Overview, Why we chose it, and Closer look. Relevant stops add an AI & energy, Ground cooling, or Winter protection card. Tabs and the small arrows change the information card; the bottom Next / Back controls change the tour stop.
- Why we chose it includes What we chose / How it works, assumptions, expandable numbers, and the supplied basis-of-design details.
- Click equipment to open Closer look inside the main card. Its selector covers all 29 objects, with equipment at the current stop listed first. Escape returns to the overview.
- Sources, alternatives and remaining checks expand inside the design notes. External links are optional citations.
- Trace power opens an overview of the battery cabinets, UPS and distribution, with continuous gold overhead feeds and a drop to every rack. Light gray cable trays and red sprinkler lines are separately labeled.
- Show boreholes flies to the ground section. A surface locator marks the field, and one actual front-edge U-loop is highlighted among all 1,024 loops. The cold battery stores cooling in rock; the electrical UPS batteries are inside the hall.
- Ground cooling explains how room air transfers heat into circulating fluid and then rock. Its Summer / Winter buttons show the two seasonal paths; air never travels down the boreholes.
- All 816 dry-cooler fans and 42 illustrative chiller fans animate using the Blender-authored rotors. Winter slows the illustration; real fan staging depends on load and temperature. Reduced-motion preferences pause the animation.
- Winter protection explains that computers produce heat, liquid carries it outdoors, and outside air takes it away. Heat must reach each exposed coil through adequate circulation; a hot campus does not protect an isolated or idle pipe. It separates normal cold-weather operation from a long cold outage with the computers off. Locate buttons show the bypass and indoor drain-down tanks. The worst-case cold-snap heat balance, tank capacities, full drainability, slopes and final control settings remain engineering work.
- AI & energy uses eight active coding hours per person daily on the top model, including repeated calls, retries and parallel agents. It explains how intensity, chip time and electricity determine capacity within each fixed-size datacenter.
- Clean view in See inside hides the main card, tags, legends and hover tips while keeping the model controls and navigation available. Toggle it off or press Escape to restore the explanations without resetting the camera or selected card. It stays on while moving between tour stops.
- X-ray reveals the hall; Ground cutaway reveals the boreholes and hides foreground terrain and meadow panels for visibility. Heat flow shows direction, reversing the seasonal ground loop in winter. Season and Labels can be changed independently.
- Full-screen mode is in the top-right corner. Reduced-motion preferences are honored.

The requirement is eight active coding hours per person daily on the top model, with no fixed daily question or task allowance. Quota-blocked waiting is excluded. The opening overview hides its “We assume…” block; the detailed workload and hardware assumptions remain inside the supporting cards.

Eight hours establishes duration, not token volume. This planning estimate treats the supplied developer study’s 28 output and 333 new input tokens/s peak rates as sustained during active hours. These are assumed aggregate rates across calls and agents, not measured Claude or personal usage. Llama 3.1 405B is the heavy hardware proxy; the 2.5× Rubin throughput gain is transferred from R1 and needs validation.

The six-site 500 MW design stays fixed. At 210 kW compute + 14 kW support and PUE 1.10, each campus fits 338 whole rack pairs: 2,028 pairs and 499.70 MW across six sites. The illustrative one-cohort result is roughly 610–640 thousand users per datacenter per day, or 3.67–3.84 million across six sites. Active periods overlap in this baseline; each user receives eight active hours. No automatic threefold shift credit or quota-wait multiplier is applied. Actual scheduling, memory bandwidth, long-context attention, response-time targets, additional storage power and reliability reserves require validation.

At that assumed intensity, eight hours processes 9,590,400 new input tokens and generates 806,400 output tokens per person. These are scenario volumes, not measured user usage or stored data. Effective context reuse is assumed, but attention, memory access and cache misses still cost resources.

One eight-hour fully loaded cohort uses about 666 MWh per campus during those hours, plus idle and transition electricity. The remaining 16 hours are not assumed to draw zero. Actual daily and annual energy require a total-load schedule. Greenhouse heat availability also follows IT load.

All 13 stops, the equipment explanations and embedded design details use this operating basis. Prior annual cooling savings, carbon-footprint shares and payback claims have been removed. Solar generation and weather-file availability are labeled separately from site electricity consumption and actual operating hours. The original borehole and cooling geometry remains a concept requiring a revised seasonal heat-balance simulation; the eight-hour requirement alone does not validate annual savings or field size.

Compute-rack purchase is about $2.64B per campus or $15.82B across six sites. Buildings, networking, context memory, electricity and operations are additional; no revised five-year total or payback is claimed. The Blender campus has 368 drawn positions, which fit the lower 190 kW case; 338 active pairs fit at the midpoint. The workload changes operating capacity without changing the physical design.

The hall wall specification encloses the stone-wool core between steel panel faces. The presentation now explains the enclosure, cut-edge and penetration details, and dust controls during installation or repair. Final assembly detailing remains engineering work.

## Deliverables

- `index.html`, `src/`, `assets/content.json`, `assets/campus.glb`, and `vendor/`: static tour.
- `blender/SEED-Cambridge.blend`: editable Blender master, with named equipment groups and cameras.
- `blender/layout.json`: dimension contract, axes and visual assumptions.
- `blender/build_scene.py`: reproducible geometry and GLB export.
- `stills/S1.png` through `S4.png`: 4K Blender renders. `S3-detail.png` is the full-size interior inset. `Power-detail.png` shows the electrical connection path. `Freeze-detail.png`, `Cooler-detail.png`, `Drain-detail.png` and `FreshAir-detail.png` show the updated thermal equipment.
- `stills/index.html`: still gallery.
- `stills/Sundai-project.png` and `stills/Sundai-project.jpg`: 2000 × 1125 Sundai project cover, using a fresh render of the existing Blender campus and the approved Amaru logo. `stills/Sundai-campus.png` is the underlying transparent render. Rebuild with `blender/render_project_cover.py`, then `node scripts/render-project-cover.mjs` (Inter fonts in `SEED_FONT_DIR` or the local Fonts folder).
- `qa/model-measurements.json`: dimensions extracted from the saved Blender model and equipment inventory checks.
- `qa/model-connectivity.json`: measured cooler connections, drain routes and separation between circuits in the saved model.
- `qa/browser-report.json`: all-stop and equipment browser acceptance checks.
- `qa/carousel-layout-report.json`: card titles, local details, scrolling and responsive-layout checks.
- `qa/model-energy-report.json`: workload arithmetic, stale-copy audit, keyboard navigation and responsive energy-card checks.
- `assets/top-model-sizing.json`: reproducible numerical results, assumptions and input hashes.
- `scripts/top_model_baseline.py`: tour-local sizing calculation and the user-approved content revision.
- `qa/thermal-design-report.json`: seasonal geothermal explanations, freeze-protection cards and clickable equipment checks.
- `qa/delivery-manifest.json`: final source and asset hashes, scene revision and verification reports.

One Blender unit is one meter. The hall center is the origin; x is east, y is north, z is up. Blender's glTF exporter converts to y-up; the viewer converts authored camera positions once.

## Rebuild and verify

```sh
python3 -I scripts/import-content.py
npm run build:model
npm run stills
npm test
```

`npm test` expects the static server running at http://127.0.0.1:4173 and an installed Chrome. Blender commands use `/Applications/Blender.app/Contents/MacOS/Blender`; set `BLENDER_BIN` for another installation. Authored with Blender 5.2.1 LTS, Three.js 0.180.0 and Playwright 1.56.1.

The optional content importer requires the original handoff, appendix/seed-basis-of-design.html and analysis files outside this repository. These are not needed to run, deploy or edit the included presentation assets. The importer reads those sources and writes only here. After importing, it applies `scripts/top_model_baseline.py`, which reads the original analysis without changing it and writes `assets/top-model-sizing.json` and the revised tour content. This prevents re-importing from restoring the superseded workload assumptions. Never edit the source handoff, punch list, analysis or appendix as part of a tour build. `assets/spec-source.md` remains the original imported source excerpt, not the revised presentation.

## Source and display boundaries

This is an illustrative design model, not a surveyed parcel or a construction document. Equipment details, surrounding buildings, vegetation and vehicles are visual interpretations within the approved dimensions. The source handoff lists the unresolved land, grid, rock-testing and vendor-engineering decisions.

The full borehole field is modeled as 32 × 32 loops. S3 uses an actual north–south mesh section at x = −37 m and an inset from the same master to make the floor pipes and racks readable. The browser cutaway removes foreground scenery as well as the field's ground surface; it does not relocate equipment. Solar frames and landscape have simplified geometry for laptop performance. The overview cameras use a wider field of view to fit the campus around the presentation card.

Revision 02 adds explanatory power feeds, UPS/distribution cabinet identities, rack drops, sprinkler headers, and distinct chip/room cooling connections. Cabinet layouts and routes are illustrative and still require engineering; no battery capacity, voltage or redundancy design is asserted. Revision 01 is preserved in `archive/seed-cambridge-01`.

Revision 03 incorporates the updated freeze and condensation design: bypass mixing valve, individual cooler isolation/drain valves and freeze sensors, indoor drain-down and expansion tanks, dew-point sensors, fresh-air drying equipment, loading-dock airlocks and insulated cold pipes. Revision 02 is preserved in `archive/seed-cambridge-02`. Winter recharge is a separate fluid path from supplying the warm hall circuit; the diagram does not send high-teens fluid into indoor coils. The fresh-air dehumidification capacity is still open and is not attributed to the 75°F room-air loop.

The supplied design text is embedded locally; affected scope, model, computer, memory, budget and efficiency sections are superseded by the user-approved revision. Campus-specific thermal details and their unresolved checks remain available. Original math and citation URLs are retained as optional references; their access permissions belong to the source project.

Revision 04 gives every outdoor fan its own Blender rotor, batched into two instanced meshes in the viewer to keep animation efficient. Equipment placement is unchanged. Existing stills are earlier static views; the chiller fans now also have visible illustrative blades. The winter card includes the liquid-to-air heat path and the eco-Air manufacturer’s requirement to verify air-assisted drainage for large coils.
