# CombineLayers

A [Glyphs 3](https://glyphsapp.com) filter plugin that combines paths from different masters and layers using boolean operations. Useful for creating cutout effects, stencil layers, inline/outline combos, and other multi-layer type designs at export time.

## How It Works

CombineLayers operates as an export filter. It takes the current master's outlines (A) and combines them with outlines from another master or layer (B) using a boolean operation. The result is applied non-destructively during font export — your source drawings are never modified.

## Boolean Operations

| Operation | Result |
|---|---|
| **Add** | Union of A and B (merge shapes together) |
| **Exclusion** | A minus B (cut away where B overlaps A) |
| **Intersection** | A intersect B (keep only where A and B overlap) |

## Path Direction Options

Each boolean operation can be paired with a path direction option that controls how B's paths are interpreted before the operation:

| Option | Behavior |
|---|---|
| **Current** | Use B's paths as-is |
| **Revert** | Reverse all of B's path directions |
| **Positive** | Resolve B to its filled area (removeOverlap + correctPathDirection) |
| **Negative** | Resolve B, then reverse all directions |

## Installation

1. Download `CombineLayers.glyphsFilter.zip`
2. Unzip and double-click `CombineLayers.glyphsFilter`
3. Restart Glyphs

The plugin will appear under *Filter > Combine Layers*.

## Usage

### Via the Dialog

1. Open *Filter > Combine Layers*
2. The current master is shown checked and grayed out (this is the base layer A)
3. Check one or more other masters/layers to combine with
4. Choose a boolean operation and path direction for each
5. Click **Create Export Instance** — this creates a new export instance with the appropriate filter parameters and opens Font Info > Exports with it selected

### Via Custom Parameters

You can also add the filter manually as a custom parameter on any instance:

**Format:**
```
Filter = CombineLayers;layerName;booleanOp;pathOp
Filter = CombineLayers;layerName;booleanOp;pathOp;parentMasterName
```

**Examples:**
```
Filter = CombineLayers;Effect;add;current
Filter = CombineLayers;Cutout;exclusion;positive
Filter = CombineLayers;Shadow;intersection;current;Regular
```

The `parentMasterName` parameter is only needed when referencing a non-master layer, to specify which master it belongs to.

### Stacking Filters

Multiple CombineLayers filters can be stacked on a single instance. They are applied in order, so each subsequent operation works on the result of the previous one.

```
Filter = CombineLayers;Shadow;add;current
Filter = CombineLayers;Cutout;exclusion;positive
```

## Compatibility

- Requires **Glyphs 3**
- Works with masters and non-master (bracket, brace, or custom) layers

## Credits

Based on [MergeLayer](https://github.com/schriftgestalt/MergeLayer) by Georg Seifert.

## License

Copyright 2026 Mans Greback.

Licensed under the Apache License, Version 2.0 (the "License");
you may not use this file except in compliance with the License.
You may obtain a copy of the License at

http://www.apache.org/licenses/LICENSE-2.0

See the [LICENSE](LICENSE) file for details.
