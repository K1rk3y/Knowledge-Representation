from flask import Blueprint, render_template, request
from rdflib import Graph, BNode
from urllib.parse import urlparse
import math
import re
from collections import defaultdict
import json
import base64 

main = Blueprint('main', __name__)

# Keep track of blank node labels
blank_node_labels = {}
next_blank_node_id = 1

@main.route('/', methods=['GET', 'POST'])
def index():
    # Reset blank node labels for each request
    global blank_node_labels, next_blank_node_id
    blank_node_labels = {}
    next_blank_node_id = 1
    
    # Load the RDF/XML file
    g = Graph()
    g.parse("app/data/ifix-it-ontology.owl", format="xml")

    prefixes = {
        '': 'http://cits3005.org/pc-ontology.owl#',  # Default namespace
    }

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
                # Strip whitespace
                s = s.strip()
                p = p.strip()
                o = o.strip()
            
                # If fields are empty, replace with variables
                s = f"?s" if not s else expand_term(s, prefixes)
                p = f"?p" if not p else expand_term(p, prefixes)
                o = f"?o" if not o else expand_term(o, prefixes)
            
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
                binding = {str(var): str(val) for var, val in row.asdict().items()}
                
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
        svg_content = '<svg width="800" height="100"><text x="400" y="50" text-anchor="middle">Enter a query to visualize the results</text></svg>'

    return render_template('index.html', 
                         svg_content=svg_content,
                         error_message=error_message)

def expand_term(term, prefixes):
    if term.startswith('?'):
        return term
    if term.startswith('<') and term.endswith('>'):
        return term  # Already a full URI
    if term.startswith('http://') or term.startswith('https://'):
        return f"<{term}>"
    if ':' in term:
        prefix, local = term.split(':', 1)
        if prefix in prefixes:
            return f"<{prefixes[prefix]}{local}>"
        else:
            raise ValueError(f"Unknown prefix '{prefix}' in term '{term}'")
    else:
        # Default namespace
        return f"<{prefixes['']}{term}>"


def get_blank_node_label(node):
    """Get a consistent human-readable label for blank nodes"""
    global next_blank_node_id
    node_str = str(node)
    if node_str not in blank_node_labels:
        blank_node_labels[node_str] = f"Anonymous-{next_blank_node_id}"
        next_blank_node_id += 1
    return blank_node_labels[node_str]

def is_blank_node(node):
    """Check if a node is a blank node"""
    node_str = str(node)
    return (isinstance(node, BNode) or
            node_str.startswith('_:') or
            re.search(r'N[0-9a-f]{30,}', node_str, re.IGNORECASE))

def get_readable_label(uri):
    """Extract human-readable labels from URIs or create labels for blank nodes"""
    if not isinstance(uri, str):
        uri = str(uri)
    
    # Handle blank nodes
    if is_blank_node(uri):
        return get_blank_node_label(uri)
    
    try:
        # Parse the URI
        parsed = urlparse(uri)
        
        # Get the path and fragment
        path = parsed.path
        fragment = parsed.fragment
        
        # If there's a fragment, use it
        if fragment:
            label = fragment
        else:
            # Split the path and get the last meaningful part
            parts = [p for p in path.split('/') if p and p != 'pc-ontology.owl']
            if parts:
                label = parts[-1]
            else:
                # If no meaningful parts found, use the whole URI
                label = uri
        
        # Handle cases where label might be encoded
        label = label.replace('%20', ' ')
        
        # Remove any remaining hashes
        label = label.split('#')[-1]
        
        # Convert CamelCase to spaces
        label = re.sub('([a-z])([A-Z])', r'\1 \2', label)
        
        return label
    except Exception as e:
        # If there's any error parsing, return the original URI
        return str(uri)

def generate_svg(triples):
    import math
    from collections import defaultdict
    import json
    import base64

    svg_elements = []
    
    # Configuration
    node_radius = 40
    node_spacing_x = 300
    node_spacing_y = 200
    margin = 100
    
    # Collect unique nodes and their relationships
    nodes = set()
    relationships = []
    for subject, predicate, obj in triples:
        nodes.add(str(subject))
        nodes.add(str(obj))
        relationships.append((str(subject), get_readable_label(predicate), str(obj)))
    
    # Build relationships for each node
    node_relationships = defaultdict(list)
    for subject, predicate_label, obj in relationships:
        # Outgoing relationship
        node_relationships[subject].append({
            'predicate': predicate_label,
            'target': get_readable_label(obj),
            'direction': 'outgoing'
        })
        # Incoming relationship
        node_relationships[obj].append({
            'predicate': predicate_label,
            'target': get_readable_label(subject),
            'direction': 'incoming'
        })
    
    # Calculate layout with blank nodes positioned differently
    nodes = list(nodes)
    regular_nodes = [n for n in nodes if not is_blank_node(n)]
    blank_nodes = [n for n in nodes if is_blank_node(n)]
    
    # Position regular nodes in a grid
    node_positions = {}
    cols = max(1, math.ceil(math.sqrt(len(regular_nodes))))
    for i, node in enumerate(regular_nodes):
        row = i // cols
        col = i % cols
        x = margin + col * node_spacing_x
        y = margin + row * node_spacing_y
        node_positions[node] = (x, y)
    
    # Position blank nodes between their connected regular nodes
    for blank_node in blank_nodes:
        connected_nodes = []
        for s, _, o in relationships:
            if s == blank_node and str(o) in node_positions:
                connected_nodes.append(str(o))
            elif o == blank_node and str(s) in node_positions:
                connected_nodes.append(str(s))
        
        if connected_nodes:
            # Position blank node between its connected nodes
            avg_x = sum(node_positions[n][0] for n in connected_nodes) / len(connected_nodes)
            avg_y = sum(node_positions[n][1] for n in connected_nodes) / len(connected_nodes)
            node_positions[blank_node] = (avg_x, avg_y - node_spacing_y / 2)
        else:
            # If no connections found, place at the bottom
            max_y = max(y for _, y in node_positions.values()) if node_positions else margin
            node_positions[blank_node] = (margin, max_y + node_spacing_y)
    
    # Add gradient definitions
    svg_elements.append('''
        <defs>
            <radialGradient id="nodeGradient">
                <stop offset="0%" stop-color="#85C1E9"/>
                <stop offset="100%" stop-color="#3498db"/>
            </radialGradient>
            <radialGradient id="blankNodeGradient">
                <stop offset="0%" stop-color="#95a5a6"/>
                <stop offset="100%" stop-color="#7f8c8d"/>
            </radialGradient>
            <marker id="arrowhead" markerWidth="10" markerHeight="7" 
                refX="9" refY="3.5" orient="auto">
                <polygon points="0 0, 10 3.5, 0 7" fill="#333"/>
            </marker>
        </defs>
    ''')
    
    # Draw relationships with curved lines
    for subject, predicate, obj in relationships:
        if subject not in node_positions or obj not in node_positions:
            continue
                
        start_x, start_y = node_positions[subject]
        end_x, end_y = node_positions[obj]
        
        # Calculate direction and shorten path to end at node border
        dx = end_x - start_x
        dy = end_y - start_y
        distance = math.hypot(dx, dy)
        if distance == 0:
            distance = 1  # Prevent division by zero
        unit_dx = dx / distance
        unit_dy = dy / distance

        # Adjust start and end points to be at the border of the nodes
        start_x += unit_dx * node_radius
        start_y += unit_dy * node_radius
        end_x -= unit_dx * node_radius
        end_y -= unit_dy * node_radius

        # Calculate control point for the curved line
        mid_x = (start_x + end_x) / 2
        mid_y = (start_y + end_y) / 2 - 60  # Adjust for a smoother curve

        path_id = f'path-{len(svg_elements)}'

        path = f'M {start_x},{start_y} Q {mid_x},{mid_y} {end_x},{end_y}'
    
        svg_elements.append(f'''
            <path id="{path_id}" d="{path}" fill="none" stroke="#333" stroke-width="2" 
                marker-end="url(#arrowhead)" opacity="0.8"/>
            <text dy="-5">
                <textPath href="#{path_id}" startOffset="50%" text-anchor="middle" fill="#333" font-size="12px">
                    {predicate}
                </textPath>
            </text>
        ''')
    
    # Draw nodes
    for node, (x, y) in node_positions.items():
        full_label = get_readable_label(node)  # Use full label for data attributes
        is_blank = is_blank_node(node)
        gradient = "url(#blankNodeGradient)" if is_blank else "url(#nodeGradient)"
        radius = node_radius * 0.8 if is_blank else node_radius

        # Truncate label if too long for display on the node
        label = full_label
        if len(label) > 15:
            label = label[:12] + '...'

        # Get relationships for this node
        relationships_data = node_relationships.get(node, [])
        relationships_json = json.dumps(relationships_data)
        encoded_relationships = base64.b64encode(relationships_json.encode('utf-8')).decode('utf-8')

        # Create the node SVG element with data attributes
        svg_elements.append(f'''
            <g class="node" transform="translate({x},{y})" 
               data-node-id="{node}" data-node-label="{full_label}" data-relationships="{encoded_relationships}">
                <circle r="{radius}" fill="{gradient}" 
                    stroke="#7f8c8d" stroke-width="{1 if is_blank else 2}"
                    opacity="0.9"
                    onmouseover="this.style.opacity = 1;"
                    onmouseout="this.style.opacity = 0.9;"/>
                <text text-anchor="middle" dy=".3em" fill="#2c3e50" 
                    font-size="{10 if is_blank else 12}px" 
                    font-weight="{400 if is_blank else 700}">{label}</text>
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
