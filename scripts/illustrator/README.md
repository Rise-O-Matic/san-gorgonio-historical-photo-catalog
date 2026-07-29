# Illustrator timeline generator

`build-timeline-from-json.jsx` turns one selected Illustrator group into a complete, data-bound timeline. It duplicates the selected master for every JSON event and generates the five-degree line, era segments, event dots, stems, and era labels.

## Prepare the master module

Group the complete representative module. In Illustrator’s Layers panel, name descendants using these tags:

| Name | Purpose |
| --- | --- |
| `field:date` | Inserts `event.date`. Point or area text is acceptable. |
| `field:headline` | Inserts `event.headline`. Use area text for automatic reflow. |
| `field:caption` | Inserts `event.caption`. Use area text for automatic reflow. |
| `field:reference_number` | Inserts the reference number. |
| `field:credit` | Inserts the source or credit line. |
| `image:photo` | Relinks an existing placed image. A clipping group is recommended. |
| `style:era` or `style:era-fill` | Applies the current era color as a fill. |
| `style:era-stroke` | Applies the current era color as a stroke. |
| `anchor:timeline` | Marks the point that must sit on the generated dot. |
| `anchor:upper` | Optional endpoint for the upper stem. |
| `anchor:lower` | Optional endpoint for the lower stem. |

Any JSON field can be used. For example, `field:rights.status` reads `event.rights.status`. The script requires at least one `field:` item.

Anchor objects can be tiny no-fill/no-stroke paths. The script reads their centers and hides the generated copies. Without `anchor:timeline`, it aligns the visible center of the group to each dot and reports a warning.

## Generate the timeline

1. Open the target Illustrator document and activate the intended artboard.
2. Select exactly one grouped master module outside any prior generated layer.
3. Choose **File → Scripts → Other Script…** and select `build-timeline-from-json.jsx`.
4. Select a schema-version-1 timeline JSON file.
5. If a previous `TIMELINE — GENERATED` layer exists, approve its replacement.

The script builds a temporary layer first. It removes the previous generated layer only after the replacement completes, so an error does not destroy the last successful output or the master.

## Coordinates and scale

JSON coordinates use full-size mural inches measured from the active artboard’s upper-left corner. `document.outputScale` converts them to Illustrator document size. The Beaumont mural defaults are 356 × 120 inches at full size and `0.1` output scale, producing a 35.6 × 12 inch Illustrator artboard.

Modules are never rotated. Their anchors are translated onto event points distributed between `startXInches` and `endXInches` on the configured ramp angle.

## Linked photographs

Relative photo paths resolve from `assets.basePath`, which itself may be absolute or relative to the JSON file. If `basePath` is blank, paths resolve from the JSON file’s folder. A missing file leaves the master placeholder intact and appears in the completion warnings.

For predictable cropping, name a clipping group `image:photo` and keep one linked `PlacedItem` inside it. The script relinks the image, scales it to cover the clipping bounds, and centers it.

## Output and reruns

The generated layer contains three named groups:

- `STRUCTURE`: underlay, era line segments, stems, and dots
- `MODULES`: one master duplicate per event
- `ERA LABELS`: generated era headings

Edit the master or JSON and rerun. Generated artwork is disposable; unrelated layers and the selected master are not modified.

The schema is in `timeline-data.schema.json`, and `examples/timeline-data.sample.json` is a four-event test file.
