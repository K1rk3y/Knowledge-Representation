from flask import Blueprint, render_template, request
from rdflib import Graph
from urllib.parse import urlparse
import math

main = Blueprint('main', __name__)

@main.route('/', methods=['GET', 'POST'])
def index():
    # Load the RDF/XML file
    g = Graph()
    g.parse("app/data/ifix-it-ontology.owl", format="xml")

    svg_content = None
    error_message = None

    if request.method == 'POST':
        try:
            # Get lists of form data
            subjects = request.form.getlist('subject[]')
            predicates = request.form.getlist('predicate[]')
            objects = request.form.getlist('object[]')

            # Initialize variables set and triples list
            variables = set()
            triple_patterns = []

            # Process each triple pattern
            for s, p, o in zip(subjects, predicates, objects):
                # If fields are empty, replace with variables
                s = f"?s" if not s.strip() else f"<{s}>" if not s.startswith('?') else s
                p = f"?p" if not p.strip() else f"<{p}>" if not p.startswith('?') else p
                o = f"?o" if not o.strip() else f"<{o}>" if not o.startswith('?') else o

                # Collect variables for SELECT clause
                for term in [s, p, o]:
                    if term.startswith('?'):
                        variables.add(term)

                triple_patterns.append(f"{s} {p} {o} .")

            # Construct SPARQL query
            where_clause = '\n    '.join(triple_patterns)
            select_clause = ' '.join(variables) if variables else '*'
            query = f"""
                SELECT {select_clause}
                WHERE {{
                    {where_clause}
                }}
            """

            # Execute query
            results = g.query(query)

            # Convert results to triples
            triples = []
            for row in results:
                # Since row is a tuple, we need to map variables to their values
                binding = {str(var): str(val) for var, val in row.asdict().items()}
                # For visualization, we need to reconstruct the triples
                for s, p, o in zip(subjects, predicates, objects):
                    s_val = binding.get(s.strip('?'), s) if s.startswith('?') else s
                    p_val = binding.get(p.strip('?'), p) if p.startswith('?') else p
                    o_val = binding.get(o.strip('?'), o) if o.startswith('?') else o
                    triples.append((s_val, p_val, o_val))

            if not triples:
                error_message = "No results found for this query."
            else:
                # Generate SVG from query results
                svg_content = generate_svg(triples)

        except Exception as e:
            error_message = f"Error executing query: {str(e)}"

    # For GET request or if no results, show empty form
    if svg_content is None and not error_message:
        # Generate default visualization with empty SVG
        svg_content = '<svg width="800" height="100"><text x="400" y="50" text-anchor="middle">Enter a query to visualize the results</text></svg>'

    return render_template('index.html', 
                         svg_content=svg_content,
                         error_message=error_message)


def get_readable_label(uri):
    """Extract human-readable labels from URIs"""
    if not isinstance(uri, str):
        uri = str(uri)
    
    # Parse the URI
    parsed = urlparse(uri)
    
    # Get the last part of the path
    label = parsed.path.split('/')[-1]
    
    # Remove any hash fragments
    label = label.split('#')[-1]
    
    # Convert CamelCase to spaces
    import re
    label = re.sub('([a-z])([A-Z])', r'\1 \2', label)
    
    return label


def generate_svg(triples):
    svg_elements = []
    
    # Configuration
    node_radius = 30
    node_spacing_x = 200
    node_spacing_y = 150
    margin = 100
    
    # Collect unique nodes and their relationships
    nodes = set()
    relationships = []
    for subject, predicate, obj in triples:
        nodes.add(str(subject))
        nodes.add(str(obj))
        relationships.append((str(subject), get_readable_label(predicate), str(obj)))
    
    # Calculate layout
    nodes = list(nodes)
    cols = math.ceil(math.sqrt(len(nodes)))
    node_positions = {}
    
    # Position nodes in a more organized grid
    for i, node in enumerate(nodes):
        row = i // cols
        col = i % cols
        x = margin + col * node_spacing_x
        y = margin + row * node_spacing_y
        node_positions[node] = (x, y)
    
    # Add gradient definitions
    svg_elements.append('''
        <defs>
            <radialGradient id="nodeGradient">
                <stop offset="0%" stop-color="#6bb9f0"/>
                <stop offset="100%" stop-color="#19b5fe"/>
            </radialGradient>
            <marker id="arrowhead" markerWidth="10" markerHeight="7" 
                refX="9" refY="3.5" orient="auto">
                <polygon points="0 0, 10 3.5, 0 7" fill="#666"/>
            </marker>
        </defs>
    ''')
    
    # Draw relationships (lines) first so they appear behind nodes
    for subject, predicate, obj in relationships:
        start = node_positions[subject]
        end = node_positions[obj]
        
        # Calculate line middle point for curved paths
        mid_x = (start[0] + end[0]) / 2
        mid_y = (start[1] + end[1]) / 2 - 40  # Control point for curve
        
        # Create curved path
        path = f'M {start[0]},{start[1]} Q {mid_x},{mid_y} {end[0]},{end[1]}'
        
        svg_elements.append(f'''
            <path d="{path}" fill="none" stroke="#666" stroke-width="2" 
                marker-end="url(#arrowhead)" opacity="0.6"/>
            <text>
                <textPath href="#text-path-{len(svg_elements)}" startOffset="50%" text-anchor="middle">
                    {predicate}
                </textPath>
            </text>
            <path id="text-path-{len(svg_elements)}" d="{path}" fill="none" stroke="none"/>
        ''')
    
    # Draw nodes
    for node, (x, y) in node_positions.items():
        label = get_readable_label(node)
        
        # Add node circle with gradient and hover effect
        svg_elements.append(f'''
            <g class="node" transform="translate({x},{y})">
                <circle r="{node_radius}" fill="url(#nodeGradient)" 
                    stroke="#2980b9" stroke-width="2"
                    opacity="0.9"
                    onmouseover="this.style.opacity = 1; this.style.r = {node_radius * 1.1}"
                    onmouseout="this.style.opacity = 0.9; this.style.r = {node_radius}"/>
                <text text-anchor="middle" dy=".3em" fill="white" 
                    font-size="12px" font-weight="bold">{label}</text>
            </g>
        ''')
    
    # Calculate SVG dimensions
    max_x = max(pos[0] for pos in node_positions.values()) + margin
    max_y = max(pos[1] for pos in node_positions.values()) + margin
    
    # Combine all elements into final SVG
    svg_content = f'''
        <svg width="{max_x}" height="{max_y}" viewBox="0 0 {max_x} {max_y}">
            <rect width="100%" height="100%" fill="#f8f9fa"/>
            {''.join(svg_elements)}
        </svg>
    '''
    
    return svg_content