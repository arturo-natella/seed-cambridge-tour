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
- Winter protection separates normal cold-weather operation from a long cold outage with the computers off. Locate buttons show the bypass and indoor drain-down tanks. Tank capacities, full drainability, slopes and final control settings remain engineering work.
- AI & energy opens on the top-model-for-every-request baseline. Four alternative mixes are labeled comparisons. All five use the same whole-facility power basis, including networking/storage support and cooling. The card contains the changed numbers, complete calculation, scope of cost and annual-energy estimates, and model-quality limitations.
- Clean view in See inside hides the main card, tags, legends and hover tips while keeping the model controls and navigation available. Toggle it off or press Escape to restore the explanations without resetting the camera or selected card. It stays on while moving between tour stops.
- X-ray reveals the hall; Ground cutaway reveals the boreholes and hides foreground terrain and meadow panels for visibility. Heat flow shows direction, reversing the seasonal ground loop in winter. Season and Labels can be changed independently.
- Full-screen mode is in the top-right corner. Reduced-motion preferences are honored.

Assumptions remain visible in the main bubbles. The revised baseline keeps the case C workload and 400-million-user target, but shows only about 26–27 million users’ equivalent workload within 500 MW on the heavy reference. Serving the full workload is estimated at 29,600–31,000 racks, 2.1–2.2 million GPUs and 7.3–7.6 GW. The $231–242B figure purchases compute racks only; no revised five-year total or payback is claimed. Llama 3.1 405B is a provisional heavy reference, not proof of best answer quality. gpt-oss-120b and DeepSeek-R1 remain comparisons.

The new calculation converts GB300-equivalent chips directly to 72-GPU Rubin racks at the assumed 2.5× per-rack throughput. This corrects the earlier 130/135 kW normalization mismatch (~4%). Each compute rack is then counted at 210 kW, with 14 kW support and PUE 1.10. The 500 MW cap is treated as total facility power before solar. Annual energy assumes full load for 8,760 hours, not forecast utilization. No additional batching/cache/concurrency savings are assumed. The old R1-specific cache capacity is not asserted for the heavy model.

The existing Blender campus remains the six-site concept’s geometric reference. Its 368 drawn rack positions fit the lower 190 kW rack-power case; at the midpoint about 338 pairs fit a campus allowance. The scene does not depict an engineered expansion to 7.3–7.6 GW.

## Deliverables

- `index.html`, `src/`, `assets/content.json`, `assets/campus.glb`, and `vendor/`: static tour.
- `blender/SEED-Cambridge.blend`: editable Blender master, with named equipment groups and cameras.
- `blender/layout.json`: dimension contract, axes and visual assumptions.
- `blender/build_scene.py`: reproducible geometry and GLB export.
- `stills/S1.png` through `S4.png`: 4K Blender renders. `S3-detail.png` is the full-size interior inset. `Power-detail.png` shows the electrical connection path. `Freeze-detail.png`, `Cooler-detail.png`, `Drain-detail.png` and `FreshAir-detail.png` show the updated thermal equipment.
- `stills/index.html`: still gallery.
- `qa/model-measurements.json`: dimensions extracted from the saved Blender model and equipment inventory checks.
- `qa/model-connectivity.json`: measured cooler connections, drain routes and separation between circuits in the saved model.
- `qa/browser-report.json`: all-stop and equipment browser acceptance checks.
- `qa/carousel-layout-report.json`: card titles, local details, scrolling and responsive-layout checks.
- `qa/model-energy-report.json`: revised workload scenarios, keyboard navigation and responsive energy-card checks.
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

The optional content importer requires the original handoff, appendix/seed-basis-of-design.html and analysis files outside this repository. These are not needed to run, deploy or edit the included presentation assets. The importer reads those sources and writes only here. After importing, it applies `scripts/top_model_baseline.py`, which reads the original analysis without changing it and writes `assets/top-model-sizing.json` and the revised tour content. This prevents re-importing from restoring the superseded fast-model baseline. Never edit the source handoff, punch list, analysis or appendix as part of a tour build. `assets/spec-source.md` remains the original imported source excerpt, not the revised presentation.

## Source and display boundaries

This is an illustrative design model, not a surveyed parcel or a construction document. Equipment details, surrounding buildings, vegetation and vehicles are visual interpretations within the approved dimensions. The source handoff lists the unresolved land, grid, rock-testing and vendor-engineering decisions.

The full borehole field is modeled as 32 × 32 loops. S3 uses an actual north–south mesh section at x = −37 m and an inset from the same master to make the floor pipes and racks readable. The browser cutaway removes foreground scenery as well as the field's ground surface; it does not relocate equipment. Solar frames and landscape have simplified geometry for laptop performance. The overview cameras use a wider field of view to fit the campus around the presentation card.

Revision 02 adds explanatory power feeds, UPS/distribution cabinet identities, rack drops, sprinkler headers, and distinct chip/room cooling connections. Cabinet layouts and routes are illustrative and still require engineering; no battery capacity, voltage or redundancy design is asserted. Revision 01 is preserved in `archive/seed-cambridge-01`.

Revision 03 incorporates the updated freeze and condensation design: bypass mixing valve, individual cooler isolation/drain valves and freeze sensors, indoor drain-down and expansion tanks, dew-point sensors, fresh-air drying equipment, loading-dock airlocks and insulated cold pipes. Revision 02 is preserved in `archive/seed-cambridge-02`. Winter recharge is a separate fluid path from supplying the warm hall circuit; the diagram does not send high-teens fluid into indoor coils. The fresh-air dehumidification capacity is still open and is not attributed to the 75°F room-air loop.

The supplied design text is embedded locally; affected scope, model, computer, memory, budget and efficiency sections are superseded by the user-approved revision. Campus-specific thermal details and their unresolved checks remain available. Original math and citation URLs are retained as optional references; their access permissions belong to the source project.
