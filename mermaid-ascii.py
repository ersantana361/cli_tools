#!/usr/bin/env python3
"""
Mermaid to ASCII Art Converter (Direct Parsing Approach)

This script parses Mermaid.js syntax directly and renders clean ASCII diagrams.
No external dependencies required - pure Python implementation.
"""

import re
import sys
import argparse
from typing import Dict, List, Tuple, Optional

class MermaidParser:
    def __init__(self):
        self.nodes = {}
        self.edges = []
        self.node_counter = 0
        
    def parse_mermaid(self, mermaid_code: str) -> Dict:
        """Parse Mermaid syntax into nodes and edges"""
        lines = mermaid_code.strip().split('\n')
        
        for line in lines:
            line = line.strip()
            if not line or line.startswith('%%') or line.startswith('graph'):
                continue
                
            # Parse different types of connections
            self._parse_line(line)
        
        return {
            'nodes': self.nodes,
            'edges': self.edges
        }
    
    def _parse_line(self, line: str):
        """Parse a single line of Mermaid syntax"""
        # Remove styling and classes
        line = re.sub(r':::[\w\-]+', '', line)
        line = re.sub(r'class \w+ [\w\-,]+', '', line)
        
        # Parse arrows and connections
        arrow_patterns = [
            r'(\w+)\s*-->\s*(\w+)',  # A --> B
            r'(\w+)\s*---\s*(\w+)',  # A --- B
            r'(\w+)\s*-\.->\s*(\w+)',  # A -.-> B
            r'(\w+)\s*==>\s*(\w+)',  # A ==> B
            r'(\w+)\s*->\s*(\w+)',   # A -> B
        ]
        
        for pattern in arrow_patterns:
            matches = re.findall(pattern, line)
            for match in matches:
                source, target = match
                self.edges.append((source, target))
        
        # Parse node definitions with labels
        node_patterns = [
            r'(\w+)\[(.*?)\]',  # A[Label]
            r'(\w+)\{(.*?)\}',  # A{Label}
            r'(\w+)\((.*?)\)',  # A(Label)
            r'(\w+)\>\s*(.*?)\s*\]',  # A>Label]
        ]
        
        for pattern in node_patterns:
            matches = re.findall(pattern, line)
            for match in matches:
                node_id, label = match
                self.nodes[node_id] = {
                    'label': label.strip(),
                    'shape': self._get_shape_from_pattern(pattern)
                }
    
    def _get_shape_from_pattern(self, pattern: str) -> str:
        """Determine node shape from regex pattern"""
        if r'\[' in pattern:
            return 'rectangle'
        elif r'\{' in pattern:
            return 'diamond'
        elif r'\(' in pattern:
            return 'rounded'
        elif r'\>' in pattern:
            return 'asymmetric'
        return 'rectangle'

class ASCIIRenderer:
    def __init__(self, width=100, compact=False):
        self.width = width
        self.compact = compact
        self.grid = []
        self.positions = {}
        
    def render(self, parsed_data: Dict) -> str:
        """Render parsed Mermaid data as ASCII art"""
        nodes = parsed_data['nodes']
        edges = parsed_data['edges']
        
        if not nodes:
            return "No nodes found in diagram"
        
        # Calculate layout
        layout = self._calculate_layout(nodes, edges)
        
        # Create grid
        height = max(pos[1] for pos in layout.values()) + 10
        self.grid = [[' ' for _ in range(self.width)] for _ in range(height)]
        
        # Draw nodes
        for node_id, (x, y) in layout.items():
            if node_id in nodes:
                self._draw_node(node_id, nodes[node_id], x, y)
        
        # Draw edges
        for source, target in edges:
            if source in layout and target in layout:
                self._draw_edge(layout[source], layout[target])
        
        # Convert grid to string
        result = []
        for row in self.grid:
            line = ''.join(row).rstrip()
            result.append(line)
        
        # Remove trailing empty lines
        while result and not result[-1]:
            result.pop()
        
        return '\n'.join(result)
    
    def _calculate_layout(self, nodes: Dict, edges: List) -> Dict:
        """Calculate node positions using a simple layered approach"""
        # Build adjacency list
        adj = {node: [] for node in nodes}
        in_degree = {node: 0 for node in nodes}
        
        for source, target in edges:
            if source in nodes and target in nodes:
                adj[source].append(target)
                in_degree[target] += 1
        
        # Topological sort to determine layers
        layers = []
        current_layer = [node for node in nodes if in_degree[node] == 0]
        
        if not current_layer:
            # Handle cycles - just use all nodes in first layer
            current_layer = list(nodes.keys())
        
        visited = set()
        
        while current_layer:
            layers.append(current_layer[:])
            next_layer = []
            
            for node in current_layer:
                visited.add(node)
                for neighbor in adj[node]:
                    if neighbor not in visited:
                        in_degree[neighbor] -= 1
                        if in_degree[neighbor] == 0:
                            next_layer.append(neighbor)
            
            current_layer = next_layer
        
        # Add any remaining nodes
        remaining = [node for node in nodes if node not in visited]
        if remaining:
            layers.append(remaining)
        
        # Calculate positions
        layout = {}
        layer_height = 8 if not self.compact else 5
        
        for layer_idx, layer in enumerate(layers):
            y = layer_idx * layer_height + 2
            layer_width = len(layer)
            
            if layer_width == 1:
                x = self.width // 2
                layout[layer[0]] = (x, y)
            else:
                spacing = min(self.width // (layer_width + 1), 20)
                start_x = (self.width - (layer_width - 1) * spacing) // 2
                
                for i, node in enumerate(layer):
                    x = start_x + i * spacing
                    layout[node] = (x, y)
        
        return layout
    
    def _draw_node(self, node_id: str, node_data: Dict, x: int, y: int):
        """Draw a node at the specified position"""
        label = node_data['label'][:15]  # Truncate long labels
        shape = node_data['shape']
        
        if shape == 'diamond':
            self._draw_diamond(label, x, y)
        elif shape == 'rounded':
            self._draw_rounded_box(label, x, y)
        else:
            self._draw_rectangle(label, x, y)
    
    def _draw_rectangle(self, label: str, x: int, y: int):
        """Draw a rectangular node"""
        width = max(len(label) + 4, 8)
        height = 3
        
        # Adjust position to center the box
        start_x = max(0, x - width // 2)
        start_y = max(0, y - height // 2)
        
        # Draw box
        for i in range(height):
            for j in range(width):
                if start_x + j < self.width and start_y + i < len(self.grid):
                    if i == 0 or i == height - 1:
                        self.grid[start_y + i][start_x + j] = '-'
                    elif j == 0 or j == width - 1:
                        self.grid[start_y + i][start_x + j] = '|'
        
        # Draw corners
        if start_y < len(self.grid) and start_x < self.width:
            self.grid[start_y][start_x] = '+'
            if start_x + width - 1 < self.width:
                self.grid[start_y][start_x + width - 1] = '+'
        if start_y + height - 1 < len(self.grid) and start_x < self.width:
            self.grid[start_y + height - 1][start_x] = '+'
            if start_x + width - 1 < self.width:
                self.grid[start_y + height - 1][start_x + width - 1] = '+'
        
        # Draw label
        if start_y + 1 < len(self.grid):
            label_start = start_x + (width - len(label)) // 2
            for i, char in enumerate(label):
                if label_start + i < self.width:
                    self.grid[start_y + 1][label_start + i] = char
    
    def _draw_diamond(self, label: str, x: int, y: int):
        """Draw a diamond-shaped node"""
        size = max(len(label) // 2 + 2, 3)
        
        # Draw diamond
        for i in range(-size, size + 1):
            for j in range(-size + abs(i), size - abs(i) + 1):
                if 0 <= y + i < len(self.grid) and 0 <= x + j < self.width:
                    if abs(i) + abs(j) == size:
                        self.grid[y + i][x + j] = '*'
        
        # Draw label
        if 0 <= y < len(self.grid):
            label_start = x - len(label) // 2
            for i, char in enumerate(label):
                if 0 <= label_start + i < self.width:
                    self.grid[y][label_start + i] = char
    
    def _draw_rounded_box(self, label: str, x: int, y: int):
        """Draw a rounded rectangular node"""
        width = max(len(label) + 4, 8)
        height = 3
        
        start_x = max(0, x - width // 2)
        start_y = max(0, y - height // 2)
        
        # Draw rounded box (similar to rectangle but with rounded corners)
        for i in range(height):
            for j in range(width):
                if start_x + j < self.width and start_y + i < len(self.grid):
                    if i == 0 or i == height - 1:
                        if j == 0 or j == width - 1:
                            self.grid[start_y + i][start_x + j] = '.'
                        else:
                            self.grid[start_y + i][start_x + j] = '-'
                    elif j == 0 or j == width - 1:
                        self.grid[start_y + i][start_x + j] = '|'
        
        # Draw label
        if start_y + 1 < len(self.grid):
            label_start = start_x + (width - len(label)) // 2
            for i, char in enumerate(label):
                if label_start + i < self.width:
                    self.grid[start_y + 1][label_start + i] = char
    
    def _draw_edge(self, start_pos: Tuple[int, int], end_pos: Tuple[int, int]):
        """Draw an edge between two positions"""
        x1, y1 = start_pos
        x2, y2 = end_pos
        
        # Simple line drawing (vertical then horizontal)
        if y1 < y2:
            # Draw vertical line down
            for y in range(y1 + 2, y2 - 1):
                if 0 <= y < len(self.grid) and 0 <= x1 < self.width:
                    if self.grid[y][x1] == ' ':
                        self.grid[y][x1] = '|'
            
            # Draw horizontal line
            if 0 <= y2 - 1 < len(self.grid):
                start_x, end_x = (x1, x2) if x1 < x2 else (x2, x1)
                for x in range(start_x, end_x + 1):
                    if 0 <= x < self.width:
                        if self.grid[y2 - 1][x] == ' ':
                            self.grid[y2 - 1][x] = '-'
            
            # Draw arrow
            if 0 <= y2 - 1 < len(self.grid) and 0 <= x2 < self.width:
                self.grid[y2 - 1][x2] = 'v'

def main():
    parser = argparse.ArgumentParser(description='Convert Mermaid.js diagrams to clean ASCII art')
    parser.add_argument('input', help='Input Mermaid file (.mmd) or - for stdin')
    parser.add_argument('-o', '--output', help='Output file (default: stdout)')
    parser.add_argument('-w', '--width', type=int, default=100, help='Diagram width (default: 100)')
    parser.add_argument('-c', '--compact', action='store_true', help='Compact layout')
    
    args = parser.parse_args()
    
    # Read input
    if args.input == '-':
        mermaid_code = sys.stdin.read()
    else:
        try:
            with open(args.input, 'r') as f:
                mermaid_code = f.read()
        except FileNotFoundError:
            print(f"Error: File '{args.input}' not found")
            sys.exit(1)
    
    # Parse and render
    parser = MermaidParser()
    parsed_data = parser.parse_mermaid(mermaid_code)
    
    renderer = ASCIIRenderer(width=args.width, compact=args.compact)
    ascii_art = renderer.render(parsed_data)
    
    # Output result
    if args.output:
        with open(args.output, 'w') as f:
            f.write(ascii_art)
        print(f"ASCII art saved to {args.output}")
    else:
        print(ascii_art)

if __name__ == "__main__":
    main()
