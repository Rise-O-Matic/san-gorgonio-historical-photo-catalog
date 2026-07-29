#target illustrator

/*
  Build Timeline from JSON
  Beaumont Library District historical mural

  Select one grouped master module, then run this script and choose a compatible
  JSON file. Named descendants of the master are treated as data bindings:

    field:date                 TextFrame receives event.date
    field:headline             TextFrame receives event.headline
    field:caption              TextFrame receives event.caption
    field:reference_number     TextFrame receives event.reference_number
    image:photo                Existing PlacedItem (or clipping group containing one)
    style:era-fill             Receives the event era fill color
    style:era-stroke           Receives the event era stroke color
    style:era                  Receives the era color as fill and/or text color
    anchor:timeline            Aligns this point to the generated event dot
    anchor:upper               Optional upper-stem endpoint
    anchor:lower               Optional lower-stem endpoint

  Output is transactional: the existing generated layer is left untouched until
  a complete replacement has been built successfully.
*/

(function () {
    "use strict";

    var SCRIPT_NAME = "Build Timeline from JSON";
    var DEFAULT_LAYER_NAME = "TIMELINE \u2014 GENERATED";
    var POINTS_PER_INCH = 72;
    var warnings = [];

    function fail(message) {
        throw new Error(message);
    }

    function trim(value) {
        return String(value === undefined || value === null ? "" : value).replace(/^\s+|\s+$/g, "");
    }

    function isArray(value) {
        return Object.prototype.toString.call(value) === "[object Array]";
    }

    function readJson(file) {
        file.encoding = "UTF-8";
        if (!file.open("r")) {
            fail("Could not open the JSON file:\n" + file.fsName);
        }
        var text = file.read();
        file.close();
        text = text.replace(/^\uFEFF/, "");
        try {
            if (typeof JSON !== "undefined" && JSON.parse) {
                return JSON.parse(text);
            }
            return eval("(" + text + ")");
        } catch (error) {
            fail("The selected file is not valid JSON.\n\n" + error.message);
        }
    }

    function hexColor(value, fallback) {
        var hex = trim(value || fallback || "#000000").replace(/^#/, "");
        if (hex.length === 3) {
            hex = hex.charAt(0) + hex.charAt(0) + hex.charAt(1) + hex.charAt(1) + hex.charAt(2) + hex.charAt(2);
        }
        if (!/^[0-9a-fA-F]{6}$/.test(hex)) {
            fail("Invalid color value: " + value);
        }
        var color = new RGBColor();
        color.red = parseInt(hex.substr(0, 2), 16);
        color.green = parseInt(hex.substr(2, 2), 16);
        color.blue = parseInt(hex.substr(4, 2), 16);
        return color;
    }

    function noColor() {
        return new NoColor();
    }

    function copyObject(source) {
        var target = {};
        var key;
        if (!source) {
            return target;
        }
        for (key in source) {
            if (source.hasOwnProperty(key)) {
                target[key] = source[key];
            }
        }
        return target;
    }

    function defaulted(value, fallback) {
        return value === undefined || value === null || value === "" ? fallback : value;
    }

    function normalizeConfig(data) {
        if (!data || Number(data.schemaVersion) !== 1) {
            fail("This script requires a schemaVersion 1 timeline JSON file.");
        }
        if (!isArray(data.events) || !data.events.length) {
            fail("The JSON file must contain a non-empty events array.");
        }
        if (!isArray(data.eras) || !data.eras.length) {
            fail("The JSON file must contain a non-empty eras array.");
        }

        var documentConfig = copyObject(data.document || {});
        documentConfig.widthInches = Number(defaulted(documentConfig.widthInches, 356));
        documentConfig.heightInches = Number(defaulted(documentConfig.heightInches, 120));
        documentConfig.outputScale = Number(defaulted(documentConfig.outputScale, 0.1));

        var layout = copyObject(data.layout || {});
        layout.angleDegrees = Number(defaulted(layout.angleDegrees, 5));
        layout.startXInches = Number(defaulted(layout.startXInches, 18));
        layout.endXInches = Number(defaulted(layout.endXInches, documentConfig.widthInches - 18));
        layout.startYInches = Number(defaulted(layout.startYInches, 28));
        layout.moduleOffsetXInches = Number(defaulted(layout.moduleOffsetXInches, 0));
        layout.moduleOffsetYInches = Number(defaulted(layout.moduleOffsetYInches, 0));
        layout.dotDiameterInches = Number(defaulted(layout.dotDiameterInches, 0.72));
        layout.dotStrokeWidthInches = Number(defaulted(layout.dotStrokeWidthInches, 0.08));
        layout.lineWidthInches = Number(defaulted(layout.lineWidthInches, 1.05));
        layout.underlayWidthInches = Number(defaulted(layout.underlayWidthInches, 1.45));
        layout.stemWidthInches = Number(defaulted(layout.stemWidthInches, 0.18));
        layout.upperStemLengthInches = Number(defaulted(layout.upperStemLengthInches, 1.2));
        layout.lowerStemLengthInches = Number(defaulted(layout.lowerStemLengthInches, 1.2));
        layout.labelOffsetYInches = Number(defaulted(layout.labelOffsetYInches, -17));
        layout.labelHeightInches = Number(defaulted(layout.labelHeightInches, 4.2));
        layout.labelFontSizeInches = Number(defaulted(layout.labelFontSizeInches, 0.72));
        layout.labelPaddingInches = Number(defaulted(layout.labelPaddingInches, 0.7));
        layout.labelCornerRadiusInches = Number(defaulted(layout.labelCornerRadiusInches, 0.25));
        layout.underlayColor = defaulted(layout.underlayColor, "#12191a");
        layout.dotStrokeColor = defaulted(layout.dotStrokeColor, "#fdfbf5");
        layout.labelTextColor = defaulted(layout.labelTextColor, "#ffffff");
        layout.labelsEnabled = defaulted(layout.labelsEnabled, true) !== false;
        layout.generatedLayerName = trim(defaulted(layout.generatedLayerName, DEFAULT_LAYER_NAME));

        if (!(documentConfig.outputScale > 0)) {
            fail("document.outputScale must be greater than zero.");
        }
        if (!(layout.endXInches > layout.startXInches)) {
            fail("layout.endXInches must be greater than layout.startXInches.");
        }
        if (Math.abs(layout.angleDegrees) > 45) {
            fail("layout.angleDegrees must be between -45 and 45 degrees.");
        }

        var eraMap = {};
        var eras = [];
        var i;
        for (i = 0; i < data.eras.length; i += 1) {
            var rawEra = data.eras[i];
            var era = {
                id: trim(defaulted(rawEra.id, "era-" + (i + 1))),
                label: trim(defaulted(rawEra.label, "Era " + (i + 1))),
                range: trim(defaulted(rawEra.range, "")),
                color: trim(defaulted(rawEra.color, "#15424a")),
                labelWidthInches: Number(defaulted(rawEra.labelWidthInches, Math.max(20, trim(defaulted(rawEra.label, "Era " + (i + 1))).length * 1.15)))
            };
            if (!era.id || eraMap[era.id]) {
                fail("Era IDs must be present and unique. Problem near era " + (i + 1) + ".");
            }
            hexColor(era.color);
            eraMap[era.id] = era;
            eras.push(era);
        }

        var events = [];
        var idMap = {};
        for (i = 0; i < data.events.length; i += 1) {
            var event = copyObject(data.events[i]);
            event.id = trim(defaulted(event.id, "event-" + (i + 1)));
            event.order = Number(defaulted(event.order, i + 1));
            if (typeof event.era === "number") {
                event.era = eras[Math.max(0, Math.min(eras.length - 1, Number(event.era)))] .id;
            }
            event.era = trim(event.era);
            if (!event.id || idMap[event.id]) {
                fail("Event IDs must be present and unique. Problem near event " + (i + 1) + ".");
            }
            if (!eraMap[event.era]) {
                fail("Event " + event.id + " references unknown era " + event.era + ".");
            }
            idMap[event.id] = true;
            events.push(event);
        }
        events.sort(function (a, b) { return a.order - b.order; });

        var seenEras = {};
        var currentEra = null;
        for (i = 0; i < events.length; i += 1) {
            if (events[i].era !== currentEra) {
                if (seenEras[events[i].era]) {
                    fail("Era assignments must be contiguous. Era " + events[i].era + " appears in more than one run.");
                }
                currentEra = events[i].era;
                seenEras[currentEra] = true;
            }
        }
        for (i = 0; i < eras.length; i += 1) {
            if (!seenEras[eras[i].id]) {
                fail("Era " + eras[i].id + " has no events.");
            }
        }

        return {
            document: documentConfig,
            layout: layout,
            eras: eras,
            eraMap: eraMap,
            events: events,
            assets: copyObject(data.assets || {})
        };
    }

    function getValue(object, path) {
        var parts = String(path).split(".");
        var value = object;
        var i;
        for (i = 0; i < parts.length; i += 1) {
            if (value === undefined || value === null) {
                return "";
            }
            value = value[parts[i]];
        }
        if (value === undefined || value === null) {
            return "";
        }
        if (isArray(value)) {
            return value.join("; ");
        }
        if (typeof value === "object") {
            try {
                return JSON.stringify(value);
            } catch (ignore) {
                return String(value);
            }
        }
        return String(value);
    }

    function getAllPageItems(root) {
        var items = [root];
        var i;
        try {
            for (i = 0; i < root.pageItems.length; i += 1) {
                items.push(root.pageItems[i]);
            }
        } catch (ignore) {}
        return items;
    }

    function findNamed(root, exactName) {
        var items = getAllPageItems(root);
        var i;
        for (i = 0; i < items.length; i += 1) {
            if (trim(items[i].name) === exactName) {
                return items[i];
            }
        }
        return null;
    }

    function getTagged(root, prefix) {
        var items = getAllPageItems(root);
        var found = [];
        var i;
        for (i = 0; i < items.length; i += 1) {
            if (trim(items[i].name).indexOf(prefix) === 0) {
                found.push(items[i]);
            }
        }
        return found;
    }

    function centerOf(item) {
        var bounds;
        try {
            bounds = item.geometricBounds;
        } catch (error) {
            bounds = item.visibleBounds;
        }
        return {
            x: (Number(bounds[0]) + Number(bounds[2])) / 2,
            y: (Number(bounds[1]) + Number(bounds[3])) / 2
        };
    }

    function boundsOf(item) {
        var bounds;
        try {
            bounds = item.visibleBounds;
        } catch (error) {
            bounds = item.geometricBounds;
        }
        return [Number(bounds[0]), Number(bounds[1]), Number(bounds[2]), Number(bounds[3])];
    }

    function findPlacedItem(item) {
        if (item.typename === "PlacedItem") {
            return item;
        }
        try {
            if (item.placedItems && item.placedItems.length) {
                return item.placedItems[0];
            }
        } catch (ignore) {}
        try {
            var all = item.pageItems;
            var i;
            for (i = 0; i < all.length; i += 1) {
                if (all[i].typename === "PlacedItem") {
                    return all[i];
                }
            }
        } catch (ignore2) {}
        return null;
    }

    function fitPlacedToBounds(placed, frameBounds) {
        var imageBounds = boundsOf(placed);
        var frameWidth = frameBounds[2] - frameBounds[0];
        var frameHeight = frameBounds[1] - frameBounds[3];
        var imageWidth = imageBounds[2] - imageBounds[0];
        var imageHeight = imageBounds[1] - imageBounds[3];
        if (!(frameWidth > 0 && frameHeight > 0 && imageWidth > 0 && imageHeight > 0)) {
            return;
        }
        var percent = Math.max(frameWidth / imageWidth, frameHeight / imageHeight) * 100;
        placed.resize(percent, percent);
        imageBounds = boundsOf(placed);
        var frameCenterX = (frameBounds[0] + frameBounds[2]) / 2;
        var frameCenterY = (frameBounds[1] + frameBounds[3]) / 2;
        var imageCenterX = (imageBounds[0] + imageBounds[2]) / 2;
        var imageCenterY = (imageBounds[1] + imageBounds[3]) / 2;
        placed.translate(frameCenterX - imageCenterX, frameCenterY - imageCenterY);
    }

    function resolveAssetFile(pathValue, jsonFile, assets) {
        var path = trim(pathValue);
        if (!path) {
            return null;
        }
        path = path.replace(/\\/g, "/");
        if (/^[A-Za-z]:\//.test(path) || /^\/\//.test(path) || /^\//.test(path)) {
            return new File(path);
        }
        var basePath = trim(assets.basePath || "");
        var baseFolder;
        if (basePath) {
            if (/^[A-Za-z]:\//.test(basePath.replace(/\\/g, "/")) || /^\/\//.test(basePath.replace(/\\/g, "/"))) {
                baseFolder = new Folder(basePath);
            } else {
                baseFolder = new Folder(jsonFile.parent.fsName + "/" + basePath);
            }
        } else {
            baseFolder = jsonFile.parent;
        }
        return new File(baseFolder.fsName + "/" + path);
    }

    function applyColorToItem(item, color, mode) {
        try {
            if (item.typename === "TextFrame") {
                item.textRange.characterAttributes.fillColor = color;
                return;
            }
            if (item.typename === "PathItem") {
                if (mode !== "stroke") {
                    item.filled = true;
                    item.fillColor = color;
                }
                if (mode === "stroke" || mode === "both") {
                    item.stroked = true;
                    item.strokeColor = color;
                }
                return;
            }
            if (item.typename === "CompoundPathItem") {
                var cp;
                for (cp = 0; cp < item.pathItems.length; cp += 1) {
                    applyColorToItem(item.pathItems[cp], color, mode);
                }
                return;
            }
            var children = item.pageItems;
            var i;
            for (i = 0; i < children.length; i += 1) {
                applyColorToItem(children[i], color, mode);
            }
        } catch (error) {
            warnings.push("Could not apply era color to " + item.name + ": " + error.message);
        }
    }

    function bindModule(module, event, era, jsonFile, assets) {
        var items = getAllPageItems(module);
        var eraColor = hexColor(era.color);
        var photoCount = 0;
        var fieldCount = 0;
        var i;
        for (i = 0; i < items.length; i += 1) {
            var item = items[i];
            var name = trim(item.name);
            if (name.indexOf("field:") === 0) {
                fieldCount += 1;
                var fieldName = trim(name.substr(6));
                if (item.typename !== "TextFrame") {
                    warnings.push(event.id + ": " + name + " is not a TextFrame.");
                } else {
                    item.contents = getValue(event, fieldName);
                    if ((fieldName === "headline" || fieldName === "caption") && typeof TextType !== "undefined" && item.kind !== TextType.AREATEXT) {
                        warnings.push(event.id + ": " + name + " is point text; use area text for automatic reflow.");
                    }
                    try {
                        if (item.overflows) {
                            warnings.push(event.id + ": " + name + " is overset.");
                        }
                    } catch (ignoreOverflow) {}
                }
            } else if (name.indexOf("image:") === 0) {
                var imageField = trim(name.substr(6));
                var imagePath = getValue(event, imageField);
                if (imagePath) {
                    var imageFile = resolveAssetFile(imagePath, jsonFile, assets);
                    var placed = findPlacedItem(item);
                    if (!imageFile || !imageFile.exists) {
                        warnings.push(event.id + ": linked image not found: " + imagePath);
                    } else if (!placed) {
                        warnings.push(event.id + ": " + name + " contains no PlacedItem to relink.");
                    } else {
                        var frameBounds = boundsOf(item);
                        placed.relink(imageFile);
                        try { placed.update(); } catch (ignoreUpdate) {}
                        if (item.typename !== "PlacedItem") {
                            fitPlacedToBounds(placed, frameBounds);
                        }
                        photoCount += 1;
                    }
                }
            } else if (name === "style:era" || name === "style:era-fill") {
                applyColorToItem(item, eraColor, "fill");
            } else if (name === "style:era-stroke") {
                applyColorToItem(item, eraColor, "stroke");
            }
        }
        return { fields: fieldCount, photos: photoCount };
    }

    function addLine(container, first, second, color, width, name) {
        var path = container.pathItems.add();
        path.setEntirePath([[first.x, first.y], [second.x, second.y]]);
        path.filled = false;
        path.stroked = true;
        path.strokeColor = color;
        path.strokeWidth = width;
        path.name = name;
        return path;
    }

    function addDot(container, point, diameter, fill, stroke, strokeWidth, name) {
        var dot = container.pathItems.ellipse(point.y + diameter / 2, point.x - diameter / 2, diameter, diameter);
        dot.filled = true;
        dot.fillColor = fill;
        dot.stroked = strokeWidth > 0;
        if (dot.stroked) {
            dot.strokeColor = stroke;
            dot.strokeWidth = strokeWidth;
        }
        dot.name = name;
        return dot;
    }

    function findFont(name) {
        if (!trim(name)) {
            return null;
        }
        try {
            return app.textFonts.getByName(name);
        } catch (error) {
            warnings.push("Font not found for era labels: " + name + ". Illustrator default used.");
            return null;
        }
    }

    function addEraLabel(container, era, point, config, scale) {
        var width = era.labelWidthInches * scale * POINTS_PER_INCH;
        var height = config.labelHeightInches * scale * POINTS_PER_INCH;
        var radius = config.labelCornerRadiusInches * scale * POINTS_PER_INCH;
        var left = point.x - width / 2;
        var top = point.y + height / 2;
        var group = container.groupItems.add();
        group.name = "era-label:" + era.id;
        var box = group.pathItems.roundedRectangle(top, left, width, height, radius, radius);
        box.filled = true;
        box.fillColor = hexColor(era.color);
        box.stroked = false;
        box.name = "era-label-background:" + era.id;
        var label = group.textFrames.add();
        label.contents = era.range ? era.label + "  " + era.range : era.label;
        label.name = "era-label-text:" + era.id;
        var fontSize = config.labelFontSizeInches * scale * POINTS_PER_INCH;
        label.textRange.characterAttributes.size = fontSize;
        label.textRange.characterAttributes.fillColor = hexColor(config.labelTextColor);
        var font = findFont(config.labelFont);
        if (font) {
            label.textRange.characterAttributes.textFont = font;
        }
        var padding = config.labelPaddingInches * scale * POINTS_PER_INCH;
        label.position = [left + padding, point.y - fontSize * 0.36];
        return group;
    }

    function findLayer(document, name) {
        var i;
        for (i = 0; i < document.layers.length; i += 1) {
            if (document.layers[i].name === name) {
                return document.layers[i];
            }
        }
        return null;
    }

    function hideAnchor(anchor) {
        if (!anchor) {
            return;
        }
        try { anchor.hidden = true; } catch (ignore) {}
    }

    function main() {
        if (app.documents.length === 0) {
            alert(SCRIPT_NAME + "\n\nOpen the Illustrator document first.");
            return;
        }
        var document = app.activeDocument;
        if (!document.selection || document.selection.length !== 1 || document.selection[0].typename !== "GroupItem") {
            alert(SCRIPT_NAME + "\n\nSelect exactly one grouped master module before running the script.");
            return;
        }
        var master = document.selection[0];
        var taggedFields = getTagged(master, "field:");
        if (!taggedFields.length) {
            alert(SCRIPT_NAME + "\n\nThe selected group contains no named data fields.\n\nName text frames field:date, field:headline, field:caption, or another field:<JSON path> in the Layers panel.");
            return;
        }

        var jsonFile = File.openDialog("Choose timeline JSON", "JSON files:*.json");
        if (!jsonFile) {
            return;
        }
        var config = normalizeConfig(readJson(jsonFile));
        var layout = config.layout;
        var scale = config.document.outputScale;
        var existing = findLayer(document, layout.generatedLayerName);
        if (master.layer && master.layer.name === layout.generatedLayerName) {
            alert(SCRIPT_NAME + "\n\nSelect a master outside the generated timeline layer.");
            return;
        }
        if (existing && !confirm("Replace the existing generated timeline layer?\n\n" + layout.generatedLayerName + "\n\nThe selected master and all other layers will remain untouched.")) {
            return;
        }

        var buildingName = layout.generatedLayerName + " (building)";
        var staleBuilding = findLayer(document, buildingName);
        if (staleBuilding) {
            try { staleBuilding.locked = false; staleBuilding.visible = true; staleBuilding.remove(); } catch (ignoreStale) {}
        }

        warnings = [];
        var building = document.layers.add();
        building.name = buildingName;
        var structureGroup = building.groupItems.add();
        structureGroup.name = "STRUCTURE";
        var modulesGroup = building.groupItems.add();
        modulesGroup.name = "MODULES";
        var labelsGroup = building.groupItems.add();
        labelsGroup.name = "ERA LABELS";

        try {
            var artboard = document.artboards[document.artboards.getActiveArtboardIndex()];
            var rect = artboard.artboardRect;
            var artboardLeft = Number(rect[0]);
            var artboardTop = Number(rect[1]);
            var expectedWidth = config.document.widthInches * scale * POINTS_PER_INCH;
            var expectedHeight = config.document.heightInches * scale * POINTS_PER_INCH;
            var actualWidth = Number(rect[2]) - Number(rect[0]);
            var actualHeight = Number(rect[1]) - Number(rect[3]);
            if (Math.abs(expectedWidth - actualWidth) > 2 || Math.abs(expectedHeight - actualHeight) > 2) {
                warnings.push("Active artboard is " + (actualWidth / POINTS_PER_INCH).toFixed(2) + " x " + (actualHeight / POINTS_PER_INCH).toFixed(2) + " in; JSON expects " + (expectedWidth / POINTS_PER_INCH).toFixed(2) + " x " + (expectedHeight / POINTS_PER_INCH).toFixed(2) + " in.");
            }

            function toDocumentPoint(xInches, yInches) {
                return {
                    x: artboardLeft + xInches * scale * POINTS_PER_INCH,
                    y: artboardTop - yInches * scale * POINTS_PER_INCH
                };
            }

            function lineYAt(xInches) {
                return layout.startYInches + (xInches - layout.startXInches) * Math.tan(layout.angleDegrees * Math.PI / 180);
            }

            var points = [];
            var count = config.events.length;
            var i;
            for (i = 0; i < count; i += 1) {
                var xInches = count === 1 ? (layout.startXInches + layout.endXInches) / 2 : layout.startXInches + (i / (count - 1)) * (layout.endXInches - layout.startXInches);
                var yInches = lineYAt(xInches);
                points.push({
                    xInches: xInches,
                    yInches: yInches,
                    documentPoint: toDocumentPoint(xInches, yInches)
                });
            }

            var underlayWidth = layout.underlayWidthInches * scale * POINTS_PER_INCH;
            addLine(structureGroup, points[0].documentPoint, points[points.length - 1].documentPoint, hexColor(layout.underlayColor), underlayWidth, "timeline-underlay");

            var eraRuns = [];
            var runStart = 0;
            for (i = 1; i <= count; i += 1) {
                if (i === count || config.events[i].era !== config.events[runStart].era) {
                    eraRuns.push({ era: config.eraMap[config.events[runStart].era], start: runStart, end: i - 1 });
                    runStart = i;
                }
            }

            var lineWidth = layout.lineWidthInches * scale * POINTS_PER_INCH;
            for (i = 0; i < eraRuns.length; i += 1) {
                var run = eraRuns[i];
                var startX = run.start === 0 ? layout.startXInches : (points[run.start - 1].xInches + points[run.start].xInches) / 2;
                var endX = run.end === count - 1 ? layout.endXInches : (points[run.end].xInches + points[run.end + 1].xInches) / 2;
                addLine(structureGroup, toDocumentPoint(startX, lineYAt(startX)), toDocumentPoint(endX, lineYAt(endX)), hexColor(run.era.color), lineWidth, "era-line:" + run.era.id);
                if (layout.labelsEnabled) {
                    var centerX = (points[run.start].xInches + points[run.end].xInches) / 2;
                    var labelPoint = toDocumentPoint(centerX, lineYAt(centerX) + layout.labelOffsetYInches);
                    addEraLabel(labelsGroup, run.era, labelPoint, layout, scale);
                }
            }

            var dotDiameter = layout.dotDiameterInches * scale * POINTS_PER_INCH;
            var dotStrokeWidth = layout.dotStrokeWidthInches * scale * POINTS_PER_INCH;
            var stemWidth = layout.stemWidthInches * scale * POINTS_PER_INCH;
            var photoRelinks = 0;
            var fieldBindings = 0;
            var usedFallbackAnchor = false;

            for (i = 0; i < count; i += 1) {
                var event = config.events[i];
                var era = config.eraMap[event.era];
                var module = master.duplicate(modulesGroup, ElementPlacement.PLACEATEND);
                module.name = "module:" + event.id;
                var timelineAnchor = findNamed(module, "anchor:timeline");
                var currentAnchor = timelineAnchor ? centerOf(timelineAnchor) : centerOf(module);
                if (!timelineAnchor) {
                    usedFallbackAnchor = true;
                }
                var target = toDocumentPoint(points[i].xInches + layout.moduleOffsetXInches, points[i].yInches + layout.moduleOffsetYInches);
                module.translate(target.x - currentAnchor.x, target.y - currentAnchor.y);

                var upperAnchor = findNamed(module, "anchor:upper");
                var lowerAnchor = findNamed(module, "anchor:lower");
                var upperPoint = upperAnchor ? centerOf(upperAnchor) : toDocumentPoint(points[i].xInches, points[i].yInches - layout.upperStemLengthInches);
                var lowerPoint = lowerAnchor ? centerOf(lowerAnchor) : toDocumentPoint(points[i].xInches, points[i].yInches + layout.lowerStemLengthInches);
                addLine(structureGroup, points[i].documentPoint, upperPoint, hexColor(era.color), stemWidth, "event-stem-upper:" + event.id);
                addLine(structureGroup, points[i].documentPoint, lowerPoint, hexColor(era.color), stemWidth, "event-stem-lower:" + event.id);
                addDot(structureGroup, points[i].documentPoint, dotDiameter, hexColor(era.color), hexColor(layout.dotStrokeColor), dotStrokeWidth, "event-dot:" + event.id);

                var binding = bindModule(module, event, era, jsonFile, config.assets);
                fieldBindings += binding.fields;
                photoRelinks += binding.photos;
                hideAnchor(timelineAnchor);
                hideAnchor(upperAnchor);
                hideAnchor(lowerAnchor);
            }

            if (usedFallbackAnchor) {
                warnings.push("The master has no anchor:timeline item, so its visible center was aligned to each dot. Add a named anchor for exact placement.");
            }
            structureGroup.zOrder(ZOrderMethod.SENDTOBACK);
            labelsGroup.zOrder(ZOrderMethod.BRINGTOFRONT);

            if (existing) {
                existing.locked = false;
                existing.visible = true;
                existing.remove();
            }
            building.name = layout.generatedLayerName;
            document.selection = null;
            master.selected = true;
            app.redraw();

            var message = SCRIPT_NAME + " complete.\n\n" +
                count + " modules\n" +
                count + " dots\n" +
                eraRuns.length + " era line segments\n" +
                fieldBindings + " field bindings\n" +
                photoRelinks + " linked photos";
            if (warnings.length) {
                message += "\n\nWarnings (" + warnings.length + "):\n";
                var warningLimit = Math.min(12, warnings.length);
                for (i = 0; i < warningLimit; i += 1) {
                    message += "\u2022 " + warnings[i] + "\n";
                }
                if (warnings.length > warningLimit) {
                    message += "\u2022 ...and " + (warnings.length - warningLimit) + " more.";
                }
            }
            alert(message);
        } catch (error) {
            try { building.locked = false; building.remove(); } catch (ignoreCleanup) {}
            alert(SCRIPT_NAME + " stopped.\n\nThe previous generated layer, master, and unrelated artwork were left intact.\n\n" + error.message + (error.line ? "\nLine: " + error.line : ""));
        }
    }

    try {
        main();
    } catch (error) {
        alert(SCRIPT_NAME + "\n\n" + error.message + (error.line ? "\nLine: " + error.line : ""));
    }
}());
