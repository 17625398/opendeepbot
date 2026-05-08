"""Knowledge Graph Visualizer

Provides visualization capabilities for knowledge graphs extracted from Hyper-Extract.

Features:
- Graph visualization using NetworkX
- DOT format output for Graphviz
- HTML visualization with D3.js
- PNG/SVG image generation
- Export to various formats
"""

import json
import logging
from typing import Dict, Any, Optional, List
from dataclasses import dataclass

logger = logging.getLogger(__name__)

try:
    import networkx as nx
    NETWORKX_AVAILABLE = True
except ImportError:
    NETWORKX_AVAILABLE = False
    logger.warning("networkx not installed, graph visualization limited")

try:
    from io import BytesIO
    try:
        import matplotlib.pyplot as plt
        MATPLOTLIB_AVAILABLE = True
    except ImportError:
        MATPLOTLIB_AVAILABLE = False
        logger.warning("matplotlib not installed, image generation disabled")
except ImportError:
    MATPLOTLIB_AVAILABLE = False


@dataclass
class VisualizationConfig:
    """Configuration for graph visualization"""
    layout: str = "spring"  # spring, circular, spectral, kk
    node_size: int = 500
    font_size: int = 10
    edge_color: str = "#999999"
    node_color: str = "#4a90d9"
    bg_color: str = "#ffffff"
    show_labels: bool = True
    format: str = "svg"  # svg, png, html, dot, json


class KnowledgeVisualizer:
    """Knowledge graph visualization tool"""
    
    def __init__(self):
        self.graph = None
    
    def load_graph(self, data: Dict[str, Any]):
        """Load graph data from extraction result"""
        if not NETWORKX_AVAILABLE:
            logger.warning("networkx not available, cannot load graph")
            return
        
        self.graph = nx.DiGraph()
        
        # Add entities as nodes
        entities = data.get("entities", [])
        for entity in entities:
            node_id = entity.get("id", entity.get("label", ""))
            label = entity.get("label", node_id)
            attributes = entity.get("attributes", {})
            self.graph.add_node(node_id, label=label, **attributes)
        
        # Add relations as edges
        relations = data.get("relations", [])
        for relation in relations:
            source = relation.get("source", "")
            target = relation.get("target", "")
            relation_type = relation.get("relation", relation.get("relation_type", ""))
            
            if source and target:
                self.graph.add_edge(source, target, label=relation_type)
        
        # Also handle knowledge_graph nested structure
        kg = data.get("knowledge_graph", {})
        if kg:
            for entity in kg.get("entities", []):
                node_id = entity.get("id", entity.get("label", ""))
                label = entity.get("label", node_id)
                attributes = entity.get("attributes", {})
                if node_id and node_id not in self.graph.nodes:
                    self.graph.add_node(node_id, label=label, **attributes)
            
            for relation in kg.get("relations", []):
                source = relation.get("source", "")
                target = relation.get("target", "")
                relation_type = relation.get("relation", relation.get("relation_type", ""))
                
                if source and target:
                    if not self.graph.has_edge(source, target):
                        self.graph.add_edge(source, target, label=relation_type)
    
    def to_networkx(self) -> Optional[nx.Graph]:
        """Get NetworkX graph object"""
        return self.graph
    
    def to_dot(self) -> str:
        """Convert graph to DOT format"""
        if not self.graph:
            return "digraph G {}"
        
        lines = ["digraph G {"]
        lines.append("    rankdir=LR;")
        lines.append('    node [shape=ellipse, style=filled, color="#4a90d9", fontname=Arial];')
        lines.append('    edge [color="#999999", fontname=Arial];')
        
        # Add nodes
        for node_id, attrs in self.graph.nodes(data=True):
            label = attrs.get("label", node_id)
            escaped_label = label.replace('"', '\\"')
            lines.append(f'    "{node_id}" [label="{escaped_label}"];')
        
        # Add edges
        for source, target, attrs in self.graph.edges(data=True):
            label = attrs.get("label", "")
            if label:
                escaped_label = label.replace('"', '\\"')
                lines.append(f'    "{source}" -> "{target}" [label="{escaped_label}"];')
            else:
                lines.append(f'    "{source}" -> "{target}";')
        
        lines.append("}")
        return "\n".join(lines)
    
    def to_json(self, indent: int = 2) -> str:
        """Convert graph to JSON format"""
        result = {
            "nodes": [],
            "edges": []
        }
        
        if self.graph:
            for node_id, attrs in self.graph.nodes(data=True):
                result["nodes"].append({
                    "id": node_id,
                    "label": attrs.get("label", node_id),
                    "attributes": {k: v for k, v in attrs.items() if k != "label"}
                })
            
            for source, target, attrs in self.graph.edges(data=True):
                result["edges"].append({
                    "source": source,
                    "target": target,
                    "label": attrs.get("label", "")
                })
        
        return json.dumps(result, indent=indent, ensure_ascii=False)
    
    def to_html(self) -> str:
        """Generate HTML visualization using D3.js"""
        json_data = self.to_json()
        
        html_template = f"""
<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <title>Knowledge Graph Visualization</title>
    <script src="https://d3js.org/d3.v7.min.js"></script>
    <style>
        body {{ font-family: Arial, sans-serif; margin: 0; padding: 20px; background: #f5f5f5; }}
        #container {{ width: 100%; height: 80vh; background: white; border-radius: 8px; box-shadow: 0 2px 10px rgba(0,0,0,0.1); }}
        .node {{ cursor: pointer; }}
        .node circle {{ fill: #4a90d9; stroke: #2c5aa0; stroke-width: 2; }}
        .node text {{ font-size: 12px; pointer-events: none; text-anchor: middle; }}
        .link {{ stroke: #999; stroke-opacity: 0.6; stroke-width: 2; }}
        .link-label {{ font-size: 10px; fill: #666; }}
        .tooltip {{ position: absolute; background: rgba(0,0,0,0.8); color: white; padding: 8px 12px; border-radius: 4px; font-size: 12px; pointer-events: none; }}
        .controls {{ margin-bottom: 15px; display: flex; gap: 10px; align-items: center; }}
        .controls button {{ padding: 8px 16px; background: #4a90d9; color: white; border: none; border-radius: 4px; cursor: pointer; }}
        .controls button:hover {{ background: #3a7bc8; }}
        .info {{ color: #666; font-size: 14px; }}
    </style>
</head>
<body>
    <div class="controls">
        <span class="info">Nodes: {len(self.graph.nodes) if self.graph else 0} | Edges: {len(self.graph.edges) if self.graph else 0}</span>
        <button onclick="downloadJSON()">Download JSON</button>
        <button onclick="downloadSVG()">Download SVG</button>
    </div>
    <div id="container"></div>
    
    <script>
        const graphData = {json_data};
        
        const width = document.getElementById('container').clientWidth;
        const height = document.getElementById('container').clientHeight;
        
        const svg = d3.select('#container')
            .append('svg')
            .attr('width', width)
            .attr('height', height);
        
        const tooltip = d3.select('body').append('div')
            .attr('class', 'tooltip')
            .style('opacity', 0);
        
        const simulation = d3.forceSimulation(graphData.nodes)
            .force('link', d3.forceLink(graphData.edges).id(d => d.id).distance(120))
            .force('charge', d3.forceManyBody().strength(-300))
            .force('center', d3.forceCenter(width / 2, height / 2))
            .force('collision', d3.forceCollide().radius(30));
        
        const link = svg.append('g')
            .selectAll('line')
            .data(graphData.edges)
            .enter().append('line')
            .attr('class', 'link');
        
        const linkLabels = svg.append('g')
            .selectAll('text')
            .data(graphData.edges)
            .enter().append('text')
            .attr('class', 'link-label')
            .text(d => d.label);
        
        const node = svg.append('g')
            .selectAll('g')
            .data(graphData.nodes)
            .enter().append('g')
            .attr('class', 'node')
            .call(d3.drag()
                .on('start', dragstarted)
                .on('drag', dragged)
                .on('end', dragended));
        
        node.append('circle')
            .attr('r', 20);
        
        node.append('text')
            .attr('dy', 35)
            .text(d => d.label.length > 10 ? d.label.substring(0, 10) + '...' : d.label);
        
        node.on('mouseover', function(event, d) {{
            tooltip.transition().duration(200).style('opacity', 0.9);
            tooltip.html(`<strong>${{d.label}}</strong><br/>ID: ${{d.id}}`)
                .style('left', (event.pageX + 10) + 'px')
                .style('top', (event.pageY - 28) + 'px');
        }})
        .on('mouseout', function() {{
            tooltip.transition().duration(500).style('opacity', 0);
        }});
        
        simulation.on('tick', () => {{
            link.attr('x1', d => d.source.x)
                .attr('y1', d => d.source.y)
                .attr('x2', d => d.target.x)
                .attr('y2', d => d.target.y);
            
            linkLabels.attr('x', d => (d.source.x + d.target.x) / 2)
                      .attr('y', d => (d.source.y + d.target.y) / 2);
            
            node.attr('transform', d => `translate(${{d.x}}, ${{d.y}})`);
        }});
        
        function dragstarted(event, d) {{
            if (!event.active) simulation.alphaTarget(0.3).restart();
            d.fx = d.x;
            d.fy = d.y;
        }}
        
        function dragged(event, d) {{
            d.fx = event.x;
            d.fy = event.y;
        }}
        
        function dragended(event, d) {{
            if (!event.active) simulation.alphaTarget(0);
            d.fx = null;
            d.fy = null;
        }}
        
        function downloadJSON() {{
            const blob = new Blob([JSON.stringify(graphData, null, 2)], {{type: 'application/json'}});
            const url = URL.createObjectURL(blob);
            const a = document.createElement('a');
            a.href = url;
            a.download = 'knowledge_graph.json';
            a.click();
            URL.revokeObjectURL(url);
        }}
        
        function downloadSVG() {{
            const svgElement = svg.node();
            const svgData = new XMLSerializer().serializeToString(svgElement);
            const blob = new Blob([svgData], {{type: 'image/svg+xml'}});
            const url = URL.createObjectURL(blob);
            const a = document.createElement('a');
            a.href = url;
            a.download = 'knowledge_graph.svg';
            a.click();
            URL.revokeObjectURL(url);
        }}
        
        window.addEventListener('resize', () => {{
            const newWidth = document.getElementById('container').clientWidth;
            const newHeight = document.getElementById('container').clientHeight;
            svg.attr('width', newWidth).attr('height', newHeight);
            simulation.force('center', d3.forceCenter(newWidth / 2, newHeight / 2));
            simulation.alpha(1).restart();
        }});
    </script>
</body>
</html>
"""
        return html_template.strip()
    
    def render_image(self, config: Optional[VisualizationConfig] = None) -> Optional[BytesIO]:
        """Render graph to image"""
        if not NETWORKX_AVAILABLE or not MATPLOTLIB_AVAILABLE:
            logger.warning("networkx or matplotlib not available")
            return None
        
        if not self.graph:
            return None
        
        config = config or VisualizationConfig()
        
        plt.figure(figsize=(12, 8))
        plt.style.use('default')
        
        # Choose layout
        if config.layout == "spring":
            pos = nx.spring_layout(self.graph, k=0.15, iterations=20)
        elif config.layout == "circular":
            pos = nx.circular_layout(self.graph)
        elif config.layout == "spectral":
            pos = nx.spectral_layout(self.graph)
        elif config.layout == "kk":
            pos = nx.kamada_kawai_layout(self.graph)
        else:
            pos = nx.spring_layout(self.graph)
        
        # Draw nodes
        nx.draw_networkx_nodes(
            self.graph, pos,
            node_size=config.node_size,
            node_color=config.node_color,
            alpha=0.8
        )
        
        # Draw edges
        nx.draw_networkx_edges(
            self.graph, pos,
            edge_color=config.edge_color,
            alpha=0.6,
            arrows=True
        )
        
        # Draw labels
        if config.show_labels:
            labels = {node: attrs.get("label", node) for node, attrs in self.graph.nodes(data=True)}
            edge_labels = {(u, v): attrs.get("label", "") for u, v, attrs in self.graph.edges(data=True)}
            
            nx.draw_networkx_labels(
                self.graph, pos, labels,
                font_size=config.font_size,
                font_color="#333333"
            )
            
            nx.draw_networkx_edge_labels(
                self.graph, pos, edge_labels,
                font_size=config.font_size - 2,
                font_color="#666666"
            )
        
        plt.axis('off')
        plt.tight_layout()
        
        buffer = BytesIO()
        plt.savefig(buffer, format=config.format, dpi=150, bbox_inches='tight')
        buffer.seek(0)
        
        plt.close()
        return buffer
    
    def export(self, format: str = "json", config: Optional[VisualizationConfig] = None) -> Any:
        """Export graph to specified format"""
        format = format.lower()
        
        if format == "json":
            return self.to_json()
        elif format == "dot":
            return self.to_dot()
        elif format == "html":
            return self.to_html()
        elif format in ["png", "svg"]:
            config = config or VisualizationConfig()
            config.format = format
            return self.render_image(config)
        elif format == "networkx":
            return self.graph
        else:
            raise ValueError(f"Unknown format: {format}")


def visualize_knowledge(data: Dict[str, Any], format: str = "json") -> Any:
    """Convenience function to visualize knowledge graph"""
    visualizer = KnowledgeVisualizer()
    visualizer.load_graph(data)
    return visualizer.export(format)
