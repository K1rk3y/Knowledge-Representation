from flask import Blueprint, render_template, request, jsonify
from rdflib import Graph, BNode, URIRef, Literal, RDF, Namespace
from rdflib.namespace import RDFS
from urllib.parse import urlparse
import math
import re
from collections import defaultdict
import json
import base64
from flask import redirect
from app.parser import parser_api

main = Blueprint('main', __name__)

blank_node_labels = {}
next_blank_node_id = 1

@main.route('/', methods=['GET', 'POST'])
def index():
    # Reset blank node labels for each request
    global blank_node_labels, next_blank_node_id
    blank_node_labels = {}
    next_blank_node_id = 1

    error_message = None
    svg_content = None
    query_results = None

    try:
        # Load the RDF/XML file
        g = Graph()
        g.parse("app/data/ifix-it-kg.owl", format="xml")
    except Exception as e:
        error_message = "ifix-it-kg.owl not found, please load the Knowledge Graph first."
        return render_template('index.html',
                               svg_content=svg_content,
                               query_results=query_results,
                               error_message=error_message)

    prefixes = {
        '': 'http://cits3005.org/pc-ontology.owl#',  # Default namespace
    }

    custom_query_prefixes = """
    PREFIX owl: <http://www.w3.org/2002/07/owl#>
    PREFIX rdf: <http://www.w3.org/1999/02/22-rdf-syntax-ns#>
    PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#>
    PREFIX onto: <http://cits3005.org/pc-ontology.owl#>
    """

    if request.method == 'POST':
        # Check if the user entered a custom SPARQL query
        custom_query = request.form.get('custom_sparql', '').strip()
        count_type = request.form.get('count_type')
        procedure_type = request.form.get('procedure_type')

        print(count_type, procedure_type)

        try:
            if count_type and procedure_type:
                if count_type == 'steps':
                    query = f"""
                    {custom_query_prefixes}
                    SELECT (COUNT(DISTINCT ?step) AS ?stepCount)
                    WHERE {{
                      ?procedure rdf:type onto:{procedure_type} .
                      ?step onto:isPartOfProcedure ?procedure .
                    }}
                    """
                else:  # count_type == 'procedure'
                    query = f"""
                    {custom_query_prefixes}
                    SELECT (COUNT(DISTINCT ?procedure) AS ?procedureCount)
                    WHERE {{
                      ?procedure rdf:type onto:{procedure_type} .
                    }}
                    """

                results = g.query(query)

                query_results = format_results(results)

            if custom_query:
                # Prepend the defined prefixes to the user's query for custom queries
                full_query = custom_query_prefixes + custom_query

                # Execute the query with default namespace (initNs)
                results = g.query(full_query, initNs=prefixes)

                # Format the results for display (text-based or table-based)
                query_results = format_results(results)

            else:
                # Handle triple pattern query if no custom SPARQL provided
                subjects = request.form.getlist('subject[]')
                predicates = request.form.getlist('predicate[]')
                objects = request.form.getlist('object[]')

                # Initialize variables set and triple patterns list
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

                # Execute triple pattern query
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
                           query_results=query_results,
                           error_message=error_message)


@main.route('/load_kg', methods=['POST'])
def load_kg():
    try:
        # Change the data file path (second param) to app\data\TEST.json and the number of objects being loaded (fourth param) to 5, if u want to see our error recogonition capabilities
        tool_report, sp_report, _, tool_report_f, sp_report_f, gen_report_f, incon_class = parser_api("app\data\ifix-it-ontology.owl", "app\data\PC.json", "app\data\ifix-it-kg.owl", 5, True)

        opt = serialize_reports(tool_report, sp_report, tool_report_f, sp_report_f, gen_report_f, incon_class)

        return jsonify({"message": opt})
    except Exception as e:
        return jsonify({"error": f"Error loading knowledge graph: {str(e)}"})


def serialize_reports(tool_report, sp_report, tool_report_f, sp_report_f, gen_report_f, incon_class):
    def serialize_dicts(dict_list):
        return '. '.join(str(d) for d in dict_list)
    
    def serialize_incon_classes(class_list):
        return "Inconsistent Classes: " + ', '.join(class_list)

    def serialize_resolved(dict_list, name):
        return f'Resolved Violations: "{serialize_dicts(dict_list)}"' if dict_list else f'Resolved Violations: "{name} contains no entries"'

    serialized_parts = []

    if tool_report_f:
        serialized_parts.append(serialize_dicts(tool_report_f))
    if sp_report_f:
        serialized_parts.append(serialize_dicts(sp_report_f))
    if gen_report_f:
        serialized_parts.append(serialize_dicts(gen_report_f))
    if incon_class:
        serialized_parts.append(serialize_incon_classes(incon_class))
   
    resolved_parts = []
    if not tool_report_f and tool_report:
        resolved_parts.append(serialize_resolved(tool_report, "tool_report"))
    if not sp_report_f and sp_report:
        resolved_parts.append(serialize_resolved(sp_report, "sp_report"))

    if resolved_parts:
        serialized_parts.append('.\n'.join(resolved_parts))

    return '. '.join(serialized_parts) if serialized_parts else "No error found"


def format_results(results):
    formatted_results = []

    # Iterate over each result row
    for row in results:
        result_row = {}
        for var, val in row.asdict().items():
            result_row[str(var)] = str(val)
        formatted_results.append(result_row)

    return formatted_results


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
    
@main.route('/add_data', methods=['GET', 'POST'])
def add_data():
    if request.method == 'POST':
        # Retrieve form data
        title = request.form['title']
        guidid = request.form['guidid']
        category = request.form['category']
        url = request.form['url']
        ancestors = request.form.getlist('ancestors[]')
        tool_names = request.form.getlist('tool_name[]')
        tool_urls = request.form.getlist('tool_url[]')
        tool_thumbnails = request.form.getlist('tool_thumbnail[]')
        step_orders = request.form.getlist('step_order[]')
        step_text_raw = request.form.getlist('step_text_raw[]')
        step_images = request.form.getlist('step_images[]')
        step_ids = request.form.getlist('step_id[]')
        tools_extracted = request.form.getlist('tools_extracted[]')

        # Construct steps
        steps = []
        for i in range(len(step_orders)):
            lines = request.form.getlist(f'step_line_text_{i}[]')
            step = {
                "Order": int(step_orders[i]),
                "Lines": [{"Text": line} for line in lines],
                "Text_raw": step_text_raw[i],
                "Images": step_images[i].split(','),  # Split comma-separated URLs
                "StepId": int(step_ids[i]),
                "Tools_extracted": tools_extracted[i].split(',')  # Split comma-separated tools
            }
            steps.append(step)

        # Construct toolbox
        toolbox = [{"Name": tool_names[i], "Url": tool_urls[i], "Thumbnail": tool_thumbnails[i]} for i in range(len(tool_names))]

        # Construct JSON structure
        data = {
            "Title": title,
            "Guidid": int(guidid),
            "Category": category,
            "Url": url,
            "Ancestors": ancestors,
            "Toolbox": toolbox,
            "Steps": steps
        }

        # Load the RDF graph
        g = Graph()
        g.parse("app/data/ifix-it-kg.owl", format="xml")
        onto = Namespace("http://cits3005.org/pc-ontology.owl#")

        # Create a URI for the procedure
        procedure_uri = URIRef(f"http://cits3005.org/pc-ontology.owl#{title.replace(' ', '_')}")
        g.add((procedure_uri, RDF.type, onto.Procedure))
        g.add((procedure_uri, onto.guidid, Literal(guidid)))
        g.add((procedure_uri, onto.category, Literal(category)))
        g.add((procedure_uri, onto.url, Literal(url)))

        # Handle ancestors (these are related to the item, not the procedure)
        item_uri = URIRef(f"http://cits3005.org/pc-ontology.owl#{category.replace(' ', '_')}")
        for ancestor in ancestors:
            ancestor_uri = URIRef(f"http://cits3005.org/pc-ontology.owl#{ancestor.replace(' ', '_')}")
            g.add((item_uri, onto.isPartOf, ancestor_uri))

        # Handle toolbox
        toolbox_uri = URIRef(f"http://cits3005.org/pc-ontology.owl#{title.replace(' ', '_')}_Toolbox")
        g.add((toolbox_uri, RDF.type, onto.Toolbox))
        g.add((toolbox_uri, onto.isForProcedure, procedure_uri))

        for i in range(len(tool_names)):
            tool_uri = URIRef(f"http://cits3005.org/pc-ontology.owl#{tool_names[i].replace(' ', '_')}")
            g.add((tool_uri, RDF.type, onto.Tool))
            g.add((tool_uri, onto.toolName, Literal(tool_names[i])))
            g.add((tool_uri, onto.toolUrl, Literal(tool_urls[i])))
            g.add((tool_uri, onto.toolThumbnail, Literal(tool_thumbnails[i])))
            g.add((toolbox_uri, onto.containsTool, tool_uri))

        # Handle steps
        for i, step in enumerate(steps):
            step_uri = URIRef(f"http://cits3005.org/pc-ontology.owl#Step_{step['StepId']}")
            g.add((step_uri, RDF.type, onto.Step))
            g.add((step_uri, onto.stepOrder, Literal(step['Order'])))
            g.add((step_uri, onto.isPartOfProcedure, procedure_uri))

            # Add raw text
            text_uri = URIRef(f"http://cits3005.org/pc-ontology.owl#Text_{step['StepId']}")
            g.add((text_uri, RDF.type, onto.Text))
            g.add((text_uri, RDFS.label, Literal(step['Text_raw'])))
            g.add((step_uri, onto.hasText, text_uri))

            # Add images
            for img_url in step['Images']:
                img_uri = URIRef(img_url)
                g.add((img_uri, RDF.type, onto.Image))
                g.add((step_uri, onto.hasImage, img_uri))

            # Add tools extracted
            for tool_name in step['Tools_extracted']:
                if tool_name != "NA":
                    tool_uri = URIRef(f"http://cits3005.org/pc-ontology.owl#{tool_name.replace(' ', '_')}")
                    g.add((step_uri, onto.usesTool, tool_uri))

            # Add lines
            for line in step['Lines']:
                line_uri = URIRef(f"http://cits3005.org/pc-ontology.owl#Line_{step['StepId']}_{i}")
                g.add((line_uri, RDF.type, onto.Line))
                g.add((line_uri, RDFS.label, Literal(line['Text'])))
                g.add((step_uri, onto.hasLine, line_uri))

        # Save the updated graph
        g.serialize("app/data/ifix-it-kg.owl", format="xml")

        return redirect('/')
    
    return render_template('add_data.html')

@main.route('/delete_data', methods=['GET', 'POST'])
def delete_data():
    if request.method == 'POST':
        # Retrieve form data (node to delete)
        title = request.form['title']

        # Load the RDF graph
        g = Graph()
        g.parse("app/data/ifix-it-kg.owl", format="xml")
        onto = Namespace("http://cits3005.org/pc-ontology.owl#")

        # Create the URI for the node based on the title
        node_uri = URIRef(f"http://cits3005.org/pc-ontology.owl#{title.replace(' ', '_')}")

        # Check if the node exists in the graph
        outgoing_triples = list(g.triples((node_uri, None, None)))  # Outgoing relationships
        incoming_triples = list(g.triples((None, None, node_uri)))  # Incoming relationships

        if outgoing_triples or incoming_triples:
            # Display the relationships to the user and ask for confirmation
            if 'confirm_delete' in request.form:
                # If user has confirmed deletion, proceed with deleting the node and its relationships
                g.remove((node_uri, None, None))
                g.remove((None, None, node_uri))

                # Save the updated graph
                g.serialize("app/data/ifix-it-kg.owl", format="xml")

                return redirect('/')

            else:
                # Display a warning about the relationships that will be affected
                outgoing_list = [(str(p), str(o)) for _, p, o in outgoing_triples]
                incoming_list = [(str(s), str(p)) for s, p, _ in incoming_triples]
                
                return render_template('delete_data.html', 
                                       outgoing_list=outgoing_list, 
                                       incoming_list=incoming_list, 
                                       title=title)

        else:
            # No relationships found, show error message
            error_message = f"Node with title '{title}' not found."
            return render_template('delete_data.html', error_message=error_message)

    return render_template('delete_data.html')




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


@main.route('/edit_data', methods=['GET', 'POST'])
def edit_data():
    if request.method == 'POST':
        # Retrieve the form data (node to search)
        title = request.form.get('title', '').strip()
        if not title:
            return render_template('edit_data.html', error_message="Please enter a valid node title.")
        # Load the RDF graph
        g = Graph()
        g.parse("app/data/ifix-it-kg.owl", format="xml")
        onto = Namespace("http://cits3005.org/pc-ontology.owl#")
        # Create the URI for the node based on the title
        node_uri = URIRef(f"http://cits3005.org/pc-ontology.owl#{title.replace(' ', '_')}")
        # Query outgoing relationships
        outgoing_query = f"""
        SELECT ?predicate ?object WHERE {{
            <{node_uri}> ?predicate ?object .
            FILTER (!isLiteral(?object))  # Filters out data properties
        }}
        """
        outgoing_data = g.query(outgoing_query)
        # Query data properties (e.g., rdfs:label for text)
        data_properties_query = f"""
        SELECT ?property ?value WHERE {{
            <{node_uri}> ?property ?value .
            FILTER (isLiteral(?value))  # Ensures only literal data properties are returned
        }}
        """
        data_properties = g.query(data_properties_query)
        outgoing_relationships = []
        data_properties_list = []
        # Collect outgoing relationships and data properties
        for row in outgoing_data:
            outgoing_relationships.append({
                "predicate": str(row["predicate"]),
                "object": str(row["object"])
            })
        for row in data_properties:
            if str(row["property"]).endswith("label"):
                data_properties_list.append({
                    "property": str(row["property"]),
                    "value": str(row["value"])
                })
        if outgoing_relationships or data_properties_list:
            return render_template('edit_data.html',
                                   title=title,
                                   outgoing_relationships=outgoing_relationships,
                                   data_properties=data_properties_list)
        else:
            error_message = f"No data found for the node '{title}'."
            return render_template('edit_data.html', error_message=error_message)
    return render_template('edit_data.html')


@main.route('/confirm_edits', methods=['POST'])
def confirm_edits():
    # Retrieve edits from the form
    data = request.json
    edits = data.get('edits', [])
    # Load the RDF graph
    g = Graph()
    g.parse("app/data/ifix-it-kg.owl", format="xml")
    onto = Namespace("http://cits3005.org/pc-ontology.owl#")
    for edit in edits:
        node_name = edit['node']
        property_name = edit['property']
        new_value = Literal(edit['new_value'])
        # Create the URI for the node and property
        node_uri = URIRef(f"http://cits3005.org/pc-ontology.owl#{node_name.replace(' ', '_')}")
        property_uri = URIRef(property_name)
        # Remove the old value and add the new one
        g.remove((node_uri, property_uri, None))  # Remove old property value
        g.add((node_uri, property_uri, new_value))  # Add the updated property value
    # Save the updated graph
    g.serialize("app/data/ifix-it-kg.owl", format="xml")
    return {"status": "success"}, 200
