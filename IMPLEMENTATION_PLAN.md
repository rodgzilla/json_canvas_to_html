# JSON Canvas to HTML Converter - Implementation Plan

## Overview
Create a Python program that converts JSON Canvas files into standalone HTML files with embedded JavaScript to visualize node graphs with animated GIFs.

## JSON Canvas Specification Summary

### Overall Structure
- Top level contains two optional arrays: `nodes` and `edges`

### Node Types
1. **Text Nodes**: Plain text with Markdown support
   - `id`, `type`, `x`, `y`, `width`, `height` (required)
   - `text` (required): Markdown-formatted text
   - `color` (optional)

2. **File Nodes**: References to system files (images, documents)
   - `id`, `type`, `x`, `y`, `width`, `height` (required)
   - `file` (required): file path
   - `subpath` (optional): heading/block reference
   - `color` (optional)

3. **Link Nodes**: URL references
   - `id`, `type`, `x`, `y`, `width`, `height` (required)
   - `url` (required)
   - `color` (optional)

4. **Group Nodes**: Container nodes
   - `id`, `type`, `x`, `y`, `width`, `height` (required)
   - `label` (optional)
   - `background`, `backgroundStyle` (optional)
   - `color` (optional)

### Edge Properties
- `id`, `fromNode`, `toNode` (required)
- `fromSide`, `toSide` (optional): `top`, `right`, `bottom`, `left`
- `fromEnd`, `toEnd` (optional): `none`, `arrow` (defaults: none, arrow)
- `color` (optional)
- `label` (optional)

### Color System
- Hex format: `"#FF0000"`
- Preset values: `"1"` through `"6"` (red through purple)

### Coordinate System
- Pixel-based integer coordinates (x, y)
- Origin at top-left
- Z-index determined by array order (first = bottom layer)

## Test Case

### Input File: `test canvas.canvas`
```json
{
  "nodes": [
    {"id":"3bb476b6d6f5169e","type":"file","file":"Images/Sport/BJJ/power_ride_leg_surf_half_nelson.gif","x":-371,"y":-154,"width":400,"height":225},
    {"id":"4e08bc8515e32920","type":"file","file":"Images/Sport/BJJ/grip_sequence.gif","x":219,"y":-126,"width":400,"height":225},
    {"id":"409f3f5484d0959f","type":"text","text":"Banana\n","x":-87,"y":137,"width":250,"height":60},
    {"id":"0c86a2c242555083","type":"file","file":"Images/Sport/BJJ/enigma_rdlr_opponent_pushes_into_us_arm_grip 1.gif","x":619,"y":260,"width":400,"height":225}
  ],
  "edges": [
    {"id":"0383e5fda2a7b2c3","fromNode":"3bb476b6d6f5169e","fromSide":"right","toNode":"4e08bc8515e32920","toSide":"left"},
    {"id":"617f6204d1ee6866","fromNode":"409f3f5484d0959f","fromSide":"top","toNode":"4e08bc8515e32920","toSide":"left"},
    {"id":"b60f33c042b7f5d7","fromNode":"0c86a2c242555083","fromSide":"top","toNode":"4e08bc8515e32920","toSide":"bottom"}
  ]
}
```

### Available Test Files
- `power_ride_leg_surf_half_nelson.gif`
- `grip_sequence.gif`
- `enigma_rdlr_opponent_pushes_into_us_arm_grip 1.gif`

### Target Browser
Chrome

## Project Structure

```
json_canvas_to_html/
├── json_canvas_converter.py    # Main converter script
├── IMPLEMENTATION_PLAN.md      # This file
└── test canvas.canvas          # Example canvas file
```

## Implementation Components

### 1. Python Script (`json_canvas_converter.py`)

#### Core Modules
- **JSON Parser**
  - Load and validate JSON canvas files
  - Handle malformed JSON gracefully

- **Node Processor**
  - Parse all node types (text, file, link, group)
  - Extract position, size, and styling information

- **Edge Processor**
  - Process connections between nodes
  - Calculate connection points based on `fromSide`/`toSide`

- **Asset Handler**
  - Resolve file paths (handle relative paths)
  - Convert images/GIFs to base64 data URLs
  - Handle missing files with placeholder or error message

- **HTML Generator**
  - Inject nodes as positioned HTML elements
  - Generate SVG for edges with Bezier curves
  - Embed all assets inline for standalone HTML

#### Command Line Interface
```bash
python json_canvas_converter.py <input.canvas> <output.html>
```

### 2. HTML/JavaScript Template

#### Structure
```html
<!DOCTYPE html>
<html>
<head>
    <style>
        /* Dark theme matching screenshot */
        /* Absolute positioning for nodes */
        /* SVG styling for edges */
    </style>
</head>
<body>
    <div id="canvas-container">
        <!-- SVG layer for edges -->
        <svg id="edges-layer"></svg>

        <!-- Nodes positioned absolutely -->
        <div id="nodes-layer"></div>
    </div>

    <script>
        /* Edge curve calculations */
        /* Dynamic rendering */
    </script>
</body>
</html>
```

#### Node Rendering
- **Text Nodes**: `<div>` with Markdown rendering
- **File Nodes**: `<img>` tags (GIFs auto-play by default)
- **Link Nodes**: `<a>` elements with URL preview
- **Group Nodes**: Container `<div>` with background

#### Edge Rendering
- SVG `<path>` elements
- Bezier curve calculations:
  - Calculate start/end points from node bounds + side
  - Control points for smooth curves
  - Handle multiple edges gracefully
- Arrow markers for `toEnd="arrow"`
- Labels positioned along curve midpoint

#### Styling Requirements
- Dark background (#1e1e1e or similar)
- Node borders and shadows
- Color application (presets 1-6 and hex)
- Font styling for text nodes
- Edge stroke width and arrow size

### 3. Edge Curve Algorithm

#### Connection Point Calculation
```
For fromSide/toSide:
- top: (x + width/2, y)
- right: (x + width, y + height/2)
- bottom: (x + width/2, y + height)
- left: (x, y + height/2)
```

#### Bezier Curve Generation
- **Quadratic Bezier** for simple curves
- Control point offset perpendicular to direct line
- Distance-based control point calculation for smooth appearance

Example SVG path:
```
M startX,startY Q controlX,controlY endX,endY
```

### 4. File Path Resolution

Handle both:
1. Relative paths in canvas file (e.g., `Images/Sport/BJJ/file.gif`)
2. Actual file locations in current directory

Strategy:
- Try path as specified in JSON
- Try basename only (strip directory path)
- Search in current directory and subdirectories
- Fallback to placeholder if not found

### 5. Color Mapping

Preset colors (1-6):
```python
PRESET_COLORS = {
    "1": "#e06c75",  # Red
    "2": "#d19a66",  # Orange
    "3": "#e5c07b",  # Yellow
    "4": "#98c379",  # Green
    "5": "#61afef",  # Blue
    "6": "#c678dd",  # Purple
}
```

## Implementation Steps

### Phase 1: Core Parser (Python)
1. Set up argument parsing (input/output files)
2. Load and parse JSON canvas file
3. Validate required fields
4. Extract nodes and edges into data structures

### Phase 2: Asset Processing (Python)
1. Implement file path resolution
2. Create base64 encoding function for binary files
3. Handle image file types (GIF, PNG, JPG)
4. Error handling for missing files

### Phase 3: HTML Template Creation
1. Create base HTML structure
2. Add CSS for dark theme and node styling
3. Implement SVG layer for edges
4. Add container with proper viewport

### Phase 4: Node Rendering
1. Generate HTML for each node type
2. Apply positioning (absolute with x/y)
3. Apply dimensions (width/height)
4. Embed base64 images for file nodes
5. Render Markdown for text nodes (basic support)

### Phase 5: Edge Rendering
1. Calculate connection points from sides
2. Generate Bezier curve paths
3. Add arrow markers
4. Apply colors and labels

### Phase 6: Integration
1. Combine all components in Python script
2. Generate complete standalone HTML
3. Test with provided test case

### Phase 7: Testing & Refinement
1. Visual comparison with reference screenshot
2. Verify GIF animation playback
3. Test edge curves and connections
4. Adjust styling to match dark theme
5. Cross-browser testing (primarily Chrome)

## Success Criteria

The implementation is complete when:

- ✅ Python script runs without errors: `python json_canvas_converter.py "test canvas.canvas" output.html`
- ✅ HTML file opens in Chrome without console errors
- ✅ All three GIFs are visible and animating
- ✅ Text node "Banana" is displayed with correct positioning
- ✅ Three edges connect nodes with smooth curves:
  - power_ride → grip_sequence (right to left)
  - Banana → grip_sequence (top to left)
  - enigma → grip_sequence (top to bottom)
- ✅ Dark background matches screenshot aesthetic
- ✅ All assets are embedded (no external dependencies)
- ✅ Visual output closely resembles reference screenshot
- ✅ File can be opened offline (standalone)

## Testing Procedure

1. Run converter:
   ```bash
   python json_canvas_converter.py "test canvas.canvas" output.html
   ```

2. Open `output.html` in Chrome

3. Verify checklist:
   - [ ] Page loads without errors
   - [ ] Dark background is displayed
   - [ ] 3 GIF nodes are visible and positioned correctly
   - [ ] 1 text node shows "Banana"
   - [ ] All 3 GIFs are animating
   - [ ] 3 curved edges connect the nodes
   - [ ] Edges connect to correct sides of nodes
   - [ ] Overall appearance matches reference screenshot

4. Check browser console (F12) for JavaScript errors

5. Test file portability (move HTML to different location and verify it still works)

## Known Challenges & Solutions

### Challenge 1: Negative Coordinates
- Nodes have negative x/y values
- **Solution**: Calculate bounding box, add offset to make all coordinates positive

### Challenge 2: File Path Resolution
- Canvas references relative paths, actual files in different location
- **Solution**: Try basename matching, search current directory

### Challenge 3: Smooth Curve Calculation
- Edges need to look curved, not straight
- **Solution**: Use quadratic Bezier with control points perpendicular to line

### Challenge 4: GIF Animation
- Ensure GIFs auto-play
- **Solution**: Use standard `<img>` tag (GIFs auto-play by default in browsers)

### Challenge 5: Viewport Sizing
- Canvas uses arbitrary coordinate space
- **Solution**: Calculate min/max bounds, set SVG viewBox and container size

## Optional Enhancements (Post-MVP)

- Interactive zoom/pan functionality
- Node click events (expand/collapse)
- Search/filter nodes
- Export back to JSON after UI modifications
- Support for group nodes with backgrounds
- Advanced Markdown rendering (tables, code blocks)
- Edge label positioning and styling
- Responsive viewport for different screen sizes

## Technical Stack

### Python (3.7+)
- Standard library only (json, base64, argparse, pathlib)
- No external dependencies for basic version

### HTML/CSS/JavaScript
- Pure vanilla JS (no frameworks required)
- SVG for edge rendering
- Optional: marked.js (CDN) for Markdown rendering

### Output Format
- Single standalone HTML file
- All assets embedded as data URLs
- Inline CSS and JavaScript
- No external dependencies or network requests

## Timeline Estimate

- Phase 1-2 (Parser + Assets): 30-45 minutes
- Phase 3-4 (HTML Template + Nodes): 45-60 minutes
- Phase 5 (Edge Rendering): 45-60 minutes
- Phase 6 (Integration): 15-30 minutes
- Phase 7 (Testing/Refinement): 30-45 minutes

**Total: 3-4 hours** for complete implementation and testing

## References

- JSON Canvas Spec: https://jsoncanvas.org/spec/1.0/
- SVG Path Documentation: https://developer.mozilla.org/en-US/docs/Web/SVG/Tutorial/Paths
- Bezier Curves: https://developer.mozilla.org/en-US/docs/Web/SVG/Tutorial/Paths#bezier_curves
