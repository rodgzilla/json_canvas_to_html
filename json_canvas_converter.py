#!/usr/bin/env python3
"""
JSON Canvas to HTML Converter

Converts JSON Canvas files (.canvas) into standalone HTML files with embedded
JavaScript for visualizing node graphs with animated GIFs.
"""

import json
import base64
import argparse
import sys
from pathlib import Path
from typing import Dict, List, Tuple, Optional


class CanvasConverter:
    """Converts JSON Canvas to standalone HTML"""

    PRESET_COLORS = {
        "1": "#e06c75",  # Red
        "2": "#d19a66",  # Orange
        "3": "#e5c07b",  # Yellow
        "4": "#98c379",  # Green
        "5": "#61afef",  # Blue
        "6": "#c678dd",  # Purple
    }

    def __init__(self, canvas_path: Path, root_dir: Optional[Path] = None):
        self.canvas_path = canvas_path
        self.canvas_dir = canvas_path.parent
        self.root_dir = root_dir
        self.canvas_data = None
        self.nodes = []
        self.edges = []

    def load_canvas(self) -> bool:
        """Load and parse the JSON canvas file"""
        try:
            with open(self.canvas_path, 'r', encoding='utf-8') as f:
                self.canvas_data = json.load(f)

            self.nodes = self.canvas_data.get('nodes', [])
            self.edges = self.canvas_data.get('edges', [])
            return True
        except Exception as e:
            print(f"Error loading canvas file: {e}", file=sys.stderr)
            return False

    def resolve_file_path(self, file_path: str) -> Optional[Path]:
        """Resolve file path from canvas reference to actual file location"""
        # Try original path
        original = Path(file_path)
        if original.is_absolute() and original.exists():
            return original

        # Try relative to root directory if provided
        if self.root_dir:
            relative_to_root = self.root_dir / file_path
            if relative_to_root.exists():
                return relative_to_root

        # Try relative to canvas directory
        relative = self.canvas_dir / file_path
        if relative.exists():
            return relative

        # Try just the basename in root directory if provided
        basename = Path(file_path).name
        if self.root_dir:
            in_root_dir = self.root_dir / basename
            if in_root_dir.exists():
                return in_root_dir

            # Search recursively in root directory
            for found_file in self.root_dir.rglob(basename):
                return found_file

        # Try just the basename in canvas directory
        in_canvas_dir = self.canvas_dir / basename
        if in_canvas_dir.exists():
            return in_canvas_dir

        # Search recursively in canvas directory
        for found_file in self.canvas_dir.rglob(basename):
            return found_file

        return None

    def file_to_data_url(self, file_path: str) -> str:
        """Convert file to base64 data URL"""
        resolved_path = self.resolve_file_path(file_path)

        if resolved_path is None:
            print(f"Warning: Could not find file: {file_path}", file=sys.stderr)
            return ""

        try:
            with open(resolved_path, 'rb') as f:
                data = f.read()

            # Determine MIME type
            suffix = resolved_path.suffix.lower()
            mime_types = {
                '.gif': 'image/gif',
                '.png': 'image/png',
                '.jpg': 'image/jpeg',
                '.jpeg': 'image/jpeg',
                '.svg': 'image/svg+xml',
            }
            mime_type = mime_types.get(suffix, 'application/octet-stream')

            # Encode to base64
            b64_data = base64.b64encode(data).decode('ascii')
            return f"data:{mime_type};base64,{b64_data}"

        except Exception as e:
            print(f"Error reading file {resolved_path}: {e}", file=sys.stderr)
            return ""

    def get_color(self, color_value: Optional[str]) -> str:
        """Convert color value to CSS color"""
        if not color_value:
            return ""

        # Check if it's a preset color
        if color_value in self.PRESET_COLORS:
            return self.PRESET_COLORS[color_value]

        # Return as-is (assume hex color)
        return color_value

    def calculate_bounds(self) -> Tuple[int, int, int, int]:
        """Calculate bounding box for all nodes"""
        if not self.nodes:
            return 0, 0, 800, 600

        min_x = min(node['x'] for node in self.nodes)
        min_y = min(node['y'] for node in self.nodes)
        max_x = max(node['x'] + node['width'] for node in self.nodes)
        max_y = max(node['y'] + node['height'] for node in self.nodes)

        # Add padding
        padding = 50
        min_x -= padding
        min_y -= padding
        max_x += padding
        max_y += padding

        return min_x, min_y, max_x - min_x, max_y - min_y

    def generate_html(self) -> str:
        """Generate standalone HTML"""
        min_x, min_y, width, height = self.calculate_bounds()

        # Generate nodes HTML
        nodes_html = []
        for node in self.nodes:
            node_html = self.generate_node_html(node, min_x, min_y)
            nodes_html.append(node_html)

        # Generate edges data for JavaScript
        edges_data = json.dumps(self.edges)
        nodes_data = json.dumps([{
            'id': node['id'],
            'x': node['x'] - min_x,
            'y': node['y'] - min_y,
            'width': node['width'],
            'height': node['height'],
        } for node in self.nodes])

        html = f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0, maximum-scale=1.0, user-scalable=no">
    <meta name="apple-mobile-web-app-capable" content="yes">
    <title>Canvas Visualization</title>
    <style>
        * {{
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }}

        body {{
            background-color: #1e1e1e;
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Oxygen, Ubuntu, Cantarell, sans-serif;
            overflow: hidden;
            color: #abb2bf;
        }}

        #viewport {{
            width: 100vw;
            height: 100vh;
            overflow: hidden;
            cursor: grab;
            position: relative;
            touch-action: none;
            -webkit-user-select: none;
            user-select: none;
        }}

        #viewport.grabbing {{
            cursor: grabbing;
        }}

        #canvas-container {{
            position: relative;
            width: {width}px;
            height: {height}px;
            transform-origin: 0 0;
            transition: transform 0.1s ease-out;
        }}

        #edges-layer {{
            position: absolute;
            top: 0;
            left: 0;
            width: 100%;
            height: 100%;
            pointer-events: none;
        }}

        #nodes-layer {{
            position: relative;
            width: 100%;
            height: 100%;
        }}

        .node {{
            position: absolute;
            border-radius: 8px;
            overflow: hidden;
        }}

        .node-text {{
            background-color: #282c34;
            border: 1px solid #3e4451;
            padding: 12px;
            color: #abb2bf;
            font-size: 14px;
            line-height: 1.5;
        }}

        .node-file {{
            background-color: #282c34;
            border: 1px solid #3e4451;
        }}

        .node-file img {{
            width: 100%;
            height: 100%;
            object-fit: cover;
            display: block;
        }}

        .node-link {{
            background-color: #282c34;
            border: 1px solid #3e4451;
            padding: 12px;
            color: #61afef;
            text-decoration: none;
            display: flex;
            align-items: center;
            justify-content: center;
        }}

        .node-group {{
            background-color: rgba(40, 44, 52, 0.5);
            border: 1px solid #3e4451;
        }}

        .edge {{
            fill: none;
            stroke: #abb2bf;
            stroke-width: 2;
        }}

        .edge-arrow {{
            fill: #abb2bf;
        }}

        #controls {{
            position: fixed;
            top: 20px;
            right: 20px;
            background-color: #282c34;
            border: 1px solid #3e4451;
            border-radius: 8px;
            padding: 12px;
            z-index: 1000;
            display: flex;
            flex-direction: column;
            gap: 8px;
        }}

        .control-btn {{
            background-color: #3e4451;
            border: none;
            color: #abb2bf;
            padding: 8px 16px;
            border-radius: 4px;
            cursor: pointer;
            font-size: 14px;
            transition: background-color 0.2s;
        }}

        .control-btn:hover {{
            background-color: #4e5461;
        }}

        .control-btn:active {{
            background-color: #2e3441;
        }}

        #zoom-level {{
            text-align: center;
            color: #61afef;
            font-size: 12px;
            padding: 4px;
        }}

        #instructions {{
            position: fixed;
            bottom: 20px;
            left: 20px;
            background-color: rgba(40, 44, 52, 0.9);
            border: 1px solid #3e4451;
            border-radius: 8px;
            padding: 12px;
            font-size: 12px;
            color: #abb2bf;
            z-index: 1000;
        }}

        #instructions div {{
            margin: 4px 0;
        }}

        /* Mobile optimizations */
        @media (max-width: 768px) {{
            #controls {{
                top: 10px;
                right: 10px;
                padding: 8px;
                gap: 6px;
            }}

            .control-btn {{
                padding: 10px 14px;
                font-size: 13px;
                min-height: 44px;
            }}

            #instructions {{
                bottom: 10px;
                left: 10px;
                padding: 8px;
                font-size: 11px;
                max-width: calc(100vw - 20px);
            }}

            #zoom-level {{
                font-size: 11px;
            }}
        }}

        @media (max-width: 480px) {{
            #instructions {{
                font-size: 10px;
                padding: 6px;
            }}

            #controls {{
                padding: 6px;
                gap: 4px;
            }}

            .control-btn {{
                padding: 8px 12px;
                font-size: 12px;
            }}
        }}
    </style>
</head>
<body>
    <div id="controls">
        <button class="control-btn" id="zoom-in">Zoom In (+)</button>
        <button class="control-btn" id="zoom-out">Zoom Out (-)</button>
        <button class="control-btn" id="zoom-reset">Reset (0)</button>
        <div id="zoom-level">100%</div>
    </div>

    <div id="instructions">
        <div><strong>Controls:</strong></div>
        <div>• Mouse wheel / Pinch: Zoom in/out</div>
        <div>• Click + drag / Touch + drag: Pan around</div>
        <div>• Buttons or +/-/0 keys: Zoom controls</div>
    </div>

    <div id="viewport">
        <div id="canvas-container">
            <svg id="edges-layer">
                <defs>
                    <marker id="arrowhead" markerWidth="10" markerHeight="10" refX="9" refY="3" orient="auto">
                        <polygon points="0 0, 10 3, 0 6" class="edge-arrow" />
                    </marker>
                </defs>
            </svg>
            <div id="nodes-layer">
                {''.join(nodes_html)}
            </div>
        </div>
    </div>

    <script>
        // Nodes and edges data
        const nodes = {nodes_data};
        const edges = {edges_data};

        // Create a map of node ID to node data
        const nodeMap = {{}};
        nodes.forEach(node => {{
            nodeMap[node.id] = node;
        }});

        // Calculate connection point based on side
        function getConnectionPoint(node, side) {{
            const x = node.x;
            const y = node.y;
            const w = node.width;
            const h = node.height;

            switch (side) {{
                case 'top':
                    return {{ x: x + w / 2, y: y }};
                case 'right':
                    return {{ x: x + w, y: y + h / 2 }};
                case 'bottom':
                    return {{ x: x + w / 2, y: y + h }};
                case 'left':
                    return {{ x: x, y: y + h / 2 }};
                default:
                    return {{ x: x + w / 2, y: y + h / 2 }};
            }}
        }}

        // Generate SVG path for edge with Bezier curve
        function generateEdgePath(edge) {{
            const fromNode = nodeMap[edge.fromNode];
            const toNode = nodeMap[edge.toNode];

            if (!fromNode || !toNode) {{
                console.warn('Missing node for edge:', edge);
                return '';
            }}

            const fromSide = edge.fromSide || 'right';
            const toSide = edge.toSide || 'left';

            const start = getConnectionPoint(fromNode, fromSide);
            const end = getConnectionPoint(toNode, toSide);

            // Calculate control points for smooth curve
            const dx = end.x - start.x;
            const dy = end.y - start.y;
            const distance = Math.sqrt(dx * dx + dy * dy);

            // Offset control points based on connection sides
            let cp1x, cp1y, cp2x, cp2y;

            const offset = Math.min(distance / 2, 100);

            switch (fromSide) {{
                case 'top':
                    cp1x = start.x;
                    cp1y = start.y - offset;
                    break;
                case 'right':
                    cp1x = start.x + offset;
                    cp1y = start.y;
                    break;
                case 'bottom':
                    cp1x = start.x;
                    cp1y = start.y + offset;
                    break;
                case 'left':
                    cp1x = start.x - offset;
                    cp1y = start.y;
                    break;
            }}

            switch (toSide) {{
                case 'top':
                    cp2x = end.x;
                    cp2y = end.y - offset;
                    break;
                case 'right':
                    cp2x = end.x + offset;
                    cp2y = end.y;
                    break;
                case 'bottom':
                    cp2x = end.x;
                    cp2y = end.y + offset;
                    break;
                case 'left':
                    cp2x = end.x - offset;
                    cp2y = end.y;
                    break;
            }}

            // Create cubic Bezier curve
            return `M ${{start.x}},${{start.y}} C ${{cp1x}},${{cp1y}} ${{cp2x}},${{cp2y}} ${{end.x}},${{end.y}}`;
        }}

        // Render edges
        const svg = document.getElementById('edges-layer');
        edges.forEach(edge => {{
            const path = document.createElementNS('http://www.w3.org/2000/svg', 'path');
            path.setAttribute('d', generateEdgePath(edge));
            path.setAttribute('class', 'edge');

            // Add arrow marker if needed
            const toEnd = edge.toEnd || 'arrow';
            if (toEnd === 'arrow') {{
                path.setAttribute('marker-end', 'url(#arrowhead)');
            }}

            svg.appendChild(path);
        }});

        // Zoom and Pan functionality
        const viewport = document.getElementById('viewport');
        const container = document.getElementById('canvas-container');
        const zoomLevelDisplay = document.getElementById('zoom-level');

        let scale = 1;
        let translateX = 0;
        let translateY = 0;
        let isDragging = false;
        let startX = 0;
        let startY = 0;

        const MIN_SCALE = 0.1;
        const MAX_SCALE = 5;
        const ZOOM_STEP = 0.1;

        function updateTransform() {{
            container.style.transform = `translate(${{translateX}}px, ${{translateY}}px) scale(${{scale}})`;
            zoomLevelDisplay.textContent = `${{Math.round(scale * 100)}}%`;
        }}

        function zoom(delta, centerX = null, centerY = null) {{
            const oldScale = scale;
            scale = Math.max(MIN_SCALE, Math.min(MAX_SCALE, scale + delta));

            // Zoom towards mouse position if provided
            if (centerX !== null && centerY !== null) {{
                const scaleRatio = scale / oldScale;
                translateX = centerX - (centerX - translateX) * scaleRatio;
                translateY = centerY - (centerY - translateY) * scaleRatio;
            }}

            updateTransform();
        }}

        function resetView() {{
            scale = 1;
            translateX = 0;
            translateY = 0;
            updateTransform();
        }}

        // Mouse wheel zoom
        viewport.addEventListener('wheel', (e) => {{
            e.preventDefault();
            const delta = e.deltaY > 0 ? -ZOOM_STEP : ZOOM_STEP;
            const rect = viewport.getBoundingClientRect();
            const centerX = e.clientX - rect.left;
            const centerY = e.clientY - rect.top;
            zoom(delta, centerX, centerY);
        }}, {{ passive: false }});

        // Drag to pan
        viewport.addEventListener('mousedown', (e) => {{
            isDragging = true;
            startX = e.clientX - translateX;
            startY = e.clientY - translateY;
            viewport.classList.add('grabbing');
        }});

        document.addEventListener('mousemove', (e) => {{
            if (!isDragging) return;
            translateX = e.clientX - startX;
            translateY = e.clientY - startY;
            updateTransform();
        }});

        document.addEventListener('mouseup', () => {{
            isDragging = false;
            viewport.classList.remove('grabbing');
        }});

        // Button controls
        document.getElementById('zoom-in').addEventListener('click', () => {{
            zoom(ZOOM_STEP);
        }});

        document.getElementById('zoom-out').addEventListener('click', () => {{
            zoom(-ZOOM_STEP);
        }});

        document.getElementById('zoom-reset').addEventListener('click', () => {{
            resetView();
        }});

        // Keyboard controls
        document.addEventListener('keydown', (e) => {{
            if (e.key === '+' || e.key === '=') {{
                e.preventDefault();
                zoom(ZOOM_STEP);
            }} else if (e.key === '-' || e.key === '_') {{
                e.preventDefault();
                zoom(-ZOOM_STEP);
            }} else if (e.key === '0') {{
                e.preventDefault();
                resetView();
            }}
        }});

        // Mobile touch support
        let lastTouchDistance = 0;
        let touchStartX = 0;
        let touchStartY = 0;
        let isTouching = false;

        function getTouchDistance(touches) {{
            const dx = touches[0].clientX - touches[1].clientX;
            const dy = touches[0].clientY - touches[1].clientY;
            return Math.sqrt(dx * dx + dy * dy);
        }}

        function getTouchCenter(touches) {{
            return {{
                x: (touches[0].clientX + touches[1].clientX) / 2,
                y: (touches[0].clientY + touches[1].clientY) / 2
            }};
        }}

        viewport.addEventListener('touchstart', (e) => {{
            if (e.touches.length === 1) {{
                // Single touch - panning
                isTouching = true;
                touchStartX = e.touches[0].clientX - translateX;
                touchStartY = e.touches[0].clientY - translateY;
                viewport.classList.add('grabbing');
            }} else if (e.touches.length === 2) {{
                // Two touches - pinch to zoom
                e.preventDefault();
                lastTouchDistance = getTouchDistance(e.touches);
            }}
        }}, {{ passive: false }});

        viewport.addEventListener('touchmove', (e) => {{
            if (e.touches.length === 1 && isTouching) {{
                // Single touch - panning
                e.preventDefault();
                translateX = e.touches[0].clientX - touchStartX;
                translateY = e.touches[0].clientY - touchStartY;
                updateTransform();
            }} else if (e.touches.length === 2) {{
                // Two touches - pinch to zoom
                e.preventDefault();
                const newDistance = getTouchDistance(e.touches);
                const center = getTouchCenter(e.touches);
                const rect = viewport.getBoundingClientRect();
                const centerX = center.x - rect.left;
                const centerY = center.y - rect.top;

                // Calculate zoom delta based on distance change
                const distanceChange = newDistance - lastTouchDistance;
                const zoomDelta = (distanceChange / 100) * ZOOM_STEP;

                zoom(zoomDelta, centerX, centerY);
                lastTouchDistance = newDistance;
            }}
        }}, {{ passive: false }});

        viewport.addEventListener('touchend', (e) => {{
            if (e.touches.length === 0) {{
                isTouching = false;
                viewport.classList.remove('grabbing');
            }} else if (e.touches.length === 1) {{
                // Reset for single touch after pinch
                touchStartX = e.touches[0].clientX - translateX;
                touchStartY = e.touches[0].clientY - translateY;
                lastTouchDistance = 0;
            }}
        }}, {{ passive: false }});

        // Initialize view centered
        updateTransform();
    </script>
</body>
</html>"""

        return html

    def generate_node_html(self, node: Dict, offset_x: int, offset_y: int) -> str:
        """Generate HTML for a single node"""
        node_id = node['id']
        node_type = node['type']
        x = node['x'] - offset_x
        y = node['y'] - offset_y
        width = node['width']
        height = node['height']
        color = self.get_color(node.get('color'))

        style = f"left: {x}px; top: {y}px; width: {width}px; height: {height}px;"
        if color:
            style += f" border-color: {color};"

        if node_type == 'text':
            text = node.get('text', '')
            # Basic Markdown-like rendering (simple newline to <br>)
            text_html = text.replace('\n', '<br>')
            return f'<div class="node node-text" style="{style}">{text_html}</div>'

        elif node_type == 'file':
            file_path = node.get('file', '')
            data_url = self.file_to_data_url(file_path)
            if data_url:
                return f'<div class="node node-file" style="{style}"><img src="{data_url}" alt="{file_path}"></div>'
            else:
                return f'<div class="node node-text" style="{style}">File not found: {file_path}</div>'

        elif node_type == 'link':
            url = node.get('url', '')
            return f'<a href="{url}" class="node node-link" style="{style}" target="_blank">{url}</a>'

        elif node_type == 'group':
            label = node.get('label', '')
            return f'<div class="node node-group" style="{style}"><div>{label}</div></div>'

        return ''

    def convert(self, output_path: Path) -> bool:
        """Main conversion method"""
        if not self.load_canvas():
            return False

        html = self.generate_html()

        try:
            with open(output_path, 'w', encoding='utf-8') as f:
                f.write(html)
            print(f"Successfully converted to: {output_path}")
            return True
        except Exception as e:
            print(f"Error writing output file: {e}", file=sys.stderr)
            return False


def main():
    parser = argparse.ArgumentParser(
        description='Convert JSON Canvas files to standalone HTML visualizations'
    )
    parser.add_argument('input', help='Input .canvas file')
    parser.add_argument('output', help='Output .html file')
    parser.add_argument(
        '--root-dir', '-r',
        type=str,
        help='Root directory for resolving file paths (useful when canvas references files with relative paths like "Images/...")'
    )

    args = parser.parse_args()

    input_path = Path(args.input)
    output_path = Path(args.output)
    root_dir = Path(args.root_dir) if args.root_dir else None

    if not input_path.exists():
        print(f"Error: Input file not found: {input_path}", file=sys.stderr)
        sys.exit(1)

    if root_dir and not root_dir.exists():
        print(f"Error: Root directory not found: {root_dir}", file=sys.stderr)
        sys.exit(1)

    converter = CanvasConverter(input_path, root_dir=root_dir)
    success = converter.convert(output_path)

    sys.exit(0 if success else 1)


if __name__ == '__main__':
    main()
