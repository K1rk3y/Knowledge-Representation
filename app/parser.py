from owlready2 import *
import json
import os
from rdflib import Graph
from pyshacl import validate
import re


def selection(file_path, num):
    objects = []
    with open(file_path, 'r') as file:
        for line in file:
            try:
                data = json.loads(line.strip())
                objects.append(data)
            except json.JSONDecodeError:
                continue
    
    return objects[:num]


def extract_parts(text_raw, noun_list):
    # Convert the text to lowercase for case-insensitive matching
    text_lower = text_raw.lower()
    
    # Initialize an empty list to store found nouns
    found_parts = []
    
    # Iterate through the noun list
    for noun in noun_list:
        # Check if the lowercase noun is in the lowercase text
        if noun.lower() in text_lower:
            found_parts.append(noun)
    
    return found_parts


def flag_hazards(text):
    warning_words = ["dangerous", "danger", "hazardous", "careful", "carefully"]
    
    pattern = re.compile(r'\b(?:' + '|'.join(warning_words) + r')\b', re.IGNORECASE)

    return bool(pattern.search(text))


def clean_string(input_string):
    # Replace spaces with underscores and encode special characters
    cleaned_string = input_string.replace(" ", "_").replace("-", "_")
    return urllib.parse.quote(cleaned_string)  # URL encode special characters


def get_or_create(cls, name):
    cleaned_name = clean_string(name)  # Generate a URI-friendly name
    instance = cls(cleaned_name)  # Use the cleaned name to create instance
    if not instance in cls.instances():
        instance.label = clean_string(name)  # Set human-readable label
        return instance
    return cls(cleaned_name)


def create_class(onto, cls, name):
    name = clean_string(name)
    cls = getattr(onto, clean_string(cls), None)
    if cls:
        instance = cls(name)
        if not instance in cls.instances():
            instance.label = name
            return instance
        return cls(name)
    else:
        # Handle the case where the class does not exist
        print(f"Class does not exist. Creating new class.")
        return get_or_create(onto.Item, name)


def parse_validation_report(report):
    # Split the report into individual constraint violation sections
    report_sections = report.split("Constraint Violation in")
    
    # Initialize the set to hold each unique violation as a dictionary
    violations = []
    
    # Check and extract the overall conformity status
    conforms_match = re.search(r"Conforms: (True|False)", report)
    if conforms_match:
        conforms_value = conforms_match.group(1) == "True"
    
    # Iterate through the sections (skip the first one as it contains the header)
    for section in report_sections[1:]:
        violation_dict = {}
        violation_dict["Conforms"] = conforms_value
        
        # Extract the violation type
        violation_type_match = re.search(r"(\S+) \(", section)
        if violation_type_match:
            violation_dict["Violation"] = violation_type_match.group(1)
        
        # Extract severity
        severity_match = re.search(r"Severity:\s*(\S+)", section)
        if severity_match:
            violation_dict["Severity"] = severity_match.group(1)
        
        # Extract source shape
        source_shape_match = re.search(r"Source Shape:\s*(\S+)", section)
        if source_shape_match:
            violation_dict["Source Shape"] = source_shape_match.group(1)
        
        # Extract focus node
        focus_node_match = re.search(r"Focus Node:\s*(<[^>]+>)", section)
        if focus_node_match:
            violation_dict["Focus Node"] = focus_node_match.group(1)
        
        # Extract value node
        value_node_match = re.search(r"Value Node:\s*(<[^>]+>)", section)
        if value_node_match:
            violation_dict["Value Node"] = value_node_match.group(1)
        
        # Extract message
        message_match = re.search(r"Message:\s*(.+)", section)
        if message_match:
            violation_dict["Message"] = message_match.group(1).strip()
        
        # Add to the list if it's unique
        if violation_dict not in violations:
            violations.append(violation_dict)
    
    return violations


def run_shacl_validation(onto, shacl_file):
    graph = onto.world.as_rdflib_graph()
    shacl_graph = Graph().parse(data=shacl_file, format="turtle")
    conforms, report, message = validate(graph, shacl_graph=shacl_graph, advanced=True)

    #print(f"Validation conforms: {conforms}")
    #print(message)
    return parse_validation_report(message)


def correct_subProcedure_violations(onto, violation_node):
    g = default_world.as_rdflib_graph()

    query = """
    PREFIX rdf: <http://www.w3.org/1999/02/22-rdf-syntax-ns#>
            PREFIX ex: <http://cits3005.org/pc-ontology.owl#>
            PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#>
            SELECT DISTINCT ?procedure ?subProcedure
            WHERE {
                {
                SELECT DISTINCT ?procedure ?subProcedure
                    WHERE {
                        ?procedure rdf:type ex:Procedure .                                 
                        ?subProcedure rdf:type ex:Sub_Procedure .
                        
                        ?procedure ex:hasSubProcedure ?subProcedure .
                        
                    }
                }
                MINUS {
                SELECT DISTINCT ?procedure ?subProcedure
                WHERE {

                    {
                    SELECT DISTINCT ?procedure ?subProcedure
                    WHERE {
                        ?procedure rdf:type ex:Procedure .
                        ?procedure ex:isForItem ?item .
                        
                        ?subProcedure rdf:type ex:Sub_Procedure .
                        ?subProcedure ex:isForItem ?subItem .

                        ?step ex:isPartOfProcedure ?procedure .
                        ?subStep ex:isPartOfProcedure ?subProcedure .
                    
                        FILTER NOT EXISTS {
                            ?otherStep ex:isPartOfProcedure ?subProcedure.
                            FILTER NOT EXISTS { ?otherStep ex:isPartOfProcedure ?procedure. }
                        }

                        {
                            {
                                SELECT ?procedure (COUNT(DISTINCT ?step) AS ?stepCount)
                                WHERE {
                                ?step ex:isPartOfProcedure ?procedure.
                                }
                                GROUP BY ?procedure
                            }
                            {
                                SELECT ?subProcedure (COUNT(DISTINCT ?subStep) AS ?subStepCount)
                                WHERE {
                                ?subStep ex:isPartOfProcedure ?subProcedure.
                                }
                                GROUP BY ?subProcedure
                            }
                            FILTER (?subStepCount < ?stepCount)
                        }
                    }
                    }

                ?subProcedure ex:isForItem ?subItem .
                ?procedure ex:isForItem ?item .

                FILTER (?item = ?subItem || EXISTS { ?subItem ex:isPartOf ?item })

                }                   
                                            
                }

            }
    """

    pairs = {}
    qres = g.query(query)
    for row in qres:
        pairs[str(row[0])] = str(str(row[1]))

    for key, val in pairs.items():
        if val == violation_node[1:-1]:
            vol_node = IRIS[val]
            sol_node = IRIS[key]
            property_name = "hasSubProcedure"

            getattr(sol_node, property_name).remove(vol_node)

            if hasattr(vol_node, property_name) and getattr(vol_node, property_name):
                continue
            else:
                vol_node.is_a.remove(onto.Sub_Procedure)


def parser_api(onto_path, data_path, save_path, n):
    # Load ontology & reasoner
    java_bin_path = r"D:\ComputerCore\Java\bin"
    os.environ["JAVA_HOME"] = java_bin_path

    onto = get_ontology(onto_path).load()

    search_list = ['battery', 'cover', 'screen']

    data = selection(data_path, n)

    # Create instances and relationships
    for item in data:
        # Create Item instance
        item_instance = create_class(onto, item['Category'], f"{item['Category']}_instance")
        
        # Create Procedure instance
        procedure_instance = get_or_create(onto.Procedure, f"{item['Title']}_Procedure")
        procedure_instance.isForItem.append(item_instance)
        
        # Create Toolbox instance
        toolbox_instance = get_or_create(onto.Toolbox, f"{item['Title']}_Toolbox")
        toolbox_instance.isForProcedure.append(procedure_instance)

        part_instance = get_or_create(onto.Part, item['Subject'])
        part_instance.isPartOf.append(item_instance)
        
        # Create Tool instances
        for tool in item['Toolbox']:
            tool_instance = get_or_create(onto.Tool, tool['Name'])
            toolbox_instance.containsTool.append(tool_instance)
        
        # Create Step instances
        for step in item['Steps']:
            step_instance = get_or_create(onto.Step, f"Step_{step['StepId']}")
            step_instance.isPartOfProcedure.append(procedure_instance)
            
            text_instance = get_or_create(onto.Text, f"Text_{step['StepId']}")
            text_instance.label = step['Text_raw']
            step_instance.hasText.append(text_instance)

            for part in extract_parts(step['Text_raw'], search_list):
                part_instance = get_or_create(onto.Part, part)
                part_instance.isPartOf.append(item_instance)

            if flag_hazards(step['Text_raw']):
                hazard_instance = get_or_create(onto.Hazard, f"Hazard_{step['StepId']}")
                step_instance.hasHazard.append(hazard_instance)
            
            # Create Image instances
            for image_url in step['Images']:
                image_instance = get_or_create(onto.Image, image_url)
                step_instance.hasImage.append(image_instance)
            
            # Link Tools to Steps
            for tool_name in step['Tools_extracted']:
                if tool_name != "NA":
                    tool_instance = get_or_create(onto.Tool, tool_name)
                    step_instance.usesTool.append(tool_instance)
        
        # Create Item hierarchy
        for ancestor in item['Ancestors']:
            ancestor_instance = get_or_create(onto.Item, ancestor)
            item_instance.isPartOf.append(ancestor_instance)

    # Compute sub-procedure relations
    for p1 in onto.Procedure.instances():
        for p2 in onto.Procedure.instances():
            if p1 != p2:
                steps_p1 = set(p1.hasStep)
                steps_p2 = set(p2.hasStep)
                if steps_p2 < steps_p1:
                    p2.is_a.append(onto.Sub_Procedure)
                    p1.hasSubProcedure.append(p2)

    tool_report = run_shacl_validation(onto, shacl_file1)
    sp_report = run_shacl_validation(onto, shacl_file2)

    for item in sp_report:
        correct_subProcedure_violations(onto, item["Focus Node"])

    gen_report = run_shacl_validation(onto, shacl_file3)

    # Run the reasoner
    with onto:
        sync_reasoner(infer_property_values=True)
        print(list(default_world.inconsistent_classes()))

    tool_report_f = run_shacl_validation(onto, shacl_file1)
    sp_report_f = run_shacl_validation(onto, shacl_file2)
    gen_report_f = run_shacl_validation(onto, shacl_file3)

    # Save the ontology
    onto.save(file=save_path, format="rdfxml")

    return tool_report, sp_report, gen_report, tool_report_f, sp_report_f, gen_report_f



shacl_file1 = '''\
@prefix sh: <http://www.w3.org/ns/shacl#> .
@prefix ex: <http://cits3005.org/pc-ontology.owl#> .
@prefix rdf: <http://www.w3.org/1999/02/22-rdf-syntax-ns#> .

ex:ToolUsageShape
  a sh:NodeShape ;
  sh:targetClass ex:Procedure ;
  sh:property [
    sh:path ex:hasStep ;
    sh:minCount 1 ;
  ] ;
  sh:property [
    sh:path [sh:inversePath ex:isForProcedure] ;
    sh:minCount 1 ;
    sh:maxCount 1 ;
  ] ;
  sh:sparql [
    sh:prefixes ex: ;
    sh:select """
      PREFIX ex: <http://cits3005.org/pc-ontology.owl#>
      SELECT $this ?step ?tool
      WHERE {
        $this ex:hasStep ?step .
        ?step ex:usesTool ?tool .
        FILTER NOT EXISTS {
          ?toolbox ex:isForProcedure $this .
          ?toolbox ex:containsTool ?tool .
        }
      }
    """ ;
  ] ;
  sh:message "Tools used in a step of this procedure did not appear in the toolbox of this procedure" .
'''



shacl_file2 = '''\
@prefix sh: <http://www.w3.org/ns/shacl#> .
@prefix ex: <http://cits3005.org/pc-ontology.owl#> .
@prefix rdf: <http://www.w3.org/1999/02/22-rdf-syntax-ns#> .

ex:subProcedureShape
  a sh:NodeShape ;
  sh:targetClass ex:Sub_Procedure ;
  sh:property [
    sh:path ex:isForItem ;
    sh:minCount 1 ;
    sh:maxCount 1 ;
  ] ;
  sh:property [
    sh:path [sh:inversePath ex:isPartOfProcedure] ;
    sh:minCount 1 ;
  ] ;
  sh:not [
    sh:property [
      sh:path rdf:type ;
      sh:sparql [
      sh:prefixes ( ex: rdf: ) ;
    sh:select """
        PREFIX rdf: <http://www.w3.org/1999/02/22-rdf-syntax-ns#>
        PREFIX ex: <http://cits3005.org/pc-ontology.owl#>
        PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#>

        SELECT DISTINCT ?procedure $this
            WHERE {

                {
                SELECT DISTINCT ?procedure $this
                WHERE {
                    ?procedure rdf:type ex:Procedure .
                    ?procedure ex:isForItem ?item .
                    
                    $this rdf:type ex:Sub_Procedure .
                    $this ex:isForItem ?subItem .

                    ?step ex:isPartOfProcedure ?procedure .
                    ?subStep ex:isPartOfProcedure $this .
                 
                    FILTER NOT EXISTS {
                        ?otherStep ex:isPartOfProcedure $this.
                        FILTER NOT EXISTS { ?otherStep ex:isPartOfProcedure ?procedure. }
                    }

                    {
                        {
                            SELECT ?procedure (COUNT(DISTINCT ?step) AS ?stepCount)
                            WHERE {
                            ?step ex:isPartOfProcedure ?procedure.
                            }
                            GROUP BY ?procedure
                        }
                        {
                            SELECT $this (COUNT(DISTINCT ?subStep) AS ?subStepCount)
                            WHERE {
                            ?subStep ex:isPartOfProcedure $this.
                            }
                            GROUP BY $this
                        }
                        FILTER (?subStepCount < ?stepCount)
                    }
                }
                }

            $this ex:isForItem ?subItem .
            ?procedure ex:isForItem ?item .

            FILTER (?item = ?subItem || EXISTS { ?subItem ex:isPartOf ?item })

            }
    """ ;
      ] ;
    ] ;
  ] ;
  sh:message "This procedure is not a valid sub-procedure" .
'''



shacl_file3 = '''\
@prefix sh: <http://www.w3.org/ns/shacl#> .
@prefix rdf: <http://www.w3.org/1999/02/22-rdf-syntax-ns#> .
@prefix rdfs: <http://www.w3.org/2000/01/rdf-schema#> .
@prefix xsd: <http://www.w3.org/2001/XMLSchema#> .
@prefix ex: <http://cits3005.org/pc-ontology.owl#> .

ex:ItemShape
    a sh:NodeShape ;
    sh:targetClass ex:Item ;
    sh:property [
        sh:path ex:hasSubclass ;
        sh:class ex:Item ;
    ], 
    [
        sh:path ex:hasPart ;
        sh:class ex:Part ;
    ] .

ex:PartShape
    a sh:NodeShape ;
    sh:targetClass ex:Part ;
    sh:property [
        sh:path ex:isPartOf ;
        sh:class ex:Item ;
    ] .

ex:StepShape
    a sh:NodeShape ;
    sh:targetClass ex:Step ;
    sh:property [
        sh:path ex:usesTool ;
        sh:class ex:Tool ;
    ], 
    [
        sh:path ex:hasImage ;
        sh:class ex:Image ;
    ], 
    [
        sh:path ex:hasText ;
        sh:class ex:Text ;
    ], 
    [
        sh:path ex:isPartOfProcedure ;
        sh:class ex:Procedure ;
    ] .

ex:ImageShape
    a sh:NodeShape ;
    sh:targetClass ex:Image ;
    sh:property [
        sh:path ex:illustratesStep ;
        sh:class ex:Step ;
    ] .

ex:ToolboxShape
    a sh:NodeShape ;
    sh:targetClass ex:Toolbox ;
    sh:property [
        sh:path ex:containsTool ;
        sh:class ex:Tool ;
    ], 
    [
        sh:path ex:isForProcedure ;
        sh:class ex:Procedure ;
    ] .

ex:TextShape
    a sh:NodeShape ;
    sh:targetClass ex:Text ;
    sh:property [
        sh:path ex:describes ;
        sh:class ex:Step ;
    ] .

ex:TransitivePropertyShape
    a sh:NodeShape ;
    sh:targetSubjectsOf ex:hasSubclass, ex:hasPart, ex:isPartOf ;
    sh:property [
        sh:path [ sh:inversePath rdf:type ] ;
        sh:class sh:TransitiveProperty ;
    ] .
'''


print(parser_api("app\data\ifix-it-ontology.owl", "app\data\TEST.json", "app\data\ifix-it-kg.owl", 5))