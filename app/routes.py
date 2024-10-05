from flask import Blueprint, render_template
from rdflib import Graph

main = Blueprint('main', __name__)

@main.route('/')
def index():
    # Load the RDF/XML file
    g = Graph()
    g.parse("app\data\ifix-it-ontology.owl", format="xml")

    # Extract triples
    triples = list(g)

    # Generate SVG elements
    svg_content = generate_svg(triples)
    
    return render_template('index.html', svg_content=svg_content)


def generate_svg(triples):
    svg_elements = []
    node_radius = 20
    node_spacing = 150  # Space between nodes
    y_offset = 100  # Initial y offset
    x_offset = 100  # Initial x offset

    node_positions = {}
    node_count = 0

    # Create nodes for each unique subject and object
    unique_nodes = set()

    for subject, predicate, obj in triples:
        unique_nodes.add(str(subject))
        unique_nodes.add(str(obj))

    # Organize nodes in a grid-like structure
    for node in unique_nodes:
        x = x_offset + (node_count % 6) * node_spacing
        y = y_offset + (node_count // 6) * node_spacing
        node_positions[node] = (x, y)

        # Create a node
        svg_elements.append(f'<circle cx="{x}" cy="{y}" r="{node_radius}" fill="lightblue" />')
        svg_elements.append(f'<text x="{x}" y="{y}" text-anchor="middle" fill="black">{node}</text>')
        
        node_count += 1

    # Draw lines connecting nodes based on triples
    for subject, predicate, obj in triples:
        subject_pos = node_positions[str(subject)]
        object_pos = node_positions[str(obj)]
        svg_elements.append(f'<line x1="{subject_pos[0]}" y1="{subject_pos[1]}" x2="{object_pos[0]}" y2="{object_pos[1]}" stroke="black" stroke-width="2" />')
        svg_elements.append(f'<text x="{(subject_pos[0] + object_pos[0]) / 2}" y="{(subject_pos[1] + object_pos[1]) / 2 - 10}" text-anchor="middle" fill="black">{predicate}</text>')

    # Calculate the overall width and height of the SVG
    svg_width = max(x_offset + ((node_count % 3) + 1) * node_spacing, 1200)  # Ensure a minimum width
    svg_height = y_offset + ((node_count // 3) + 1) * node_spacing

    # Combine all SVG elements
    svg_content = f"<svg width='{svg_width}' height='{svg_height}'>{''.join(svg_elements)}</svg>"
    
    return svg_content


