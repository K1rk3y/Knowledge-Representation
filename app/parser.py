from owlready2 import *
import json
import os
from rdflib import Graph, Namespace
from pyshacl import validate

java_bin_path = r"D:\ComputerCore\Java\bin"
os.environ["JAVA_HOME"] = java_bin_path

onto = get_ontology(r"app\data\ifix-it-ontology.owl").load()


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


def create_class(cls, name):
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
        print(f"Class {cls} does not exist.")
        return None


search_list = ['battery', 'cover', 'screen']

data = selection(r"app\data\TEST.json", 5)
# Create instances and relationships
for item in data:
    # Create Item instance
    item_instance = create_class(item['Category'], f"{item['Category']}_instance")
    
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
                # print(p1, p2)
                p2.is_a.append(onto.Sub_Procedure)



shacl_file = '''\
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
    sh:message "Tools used in a step of this procedure did not appear in the toolbox of this procedure" ;
  ] .
'''



def run_shacl_validation():
    graph = onto.world.as_rdflib_graph()
    shacl_graph = Graph().parse(data=shacl_file, format="turtle")
    conforms, report, message = validate(graph, shacl_graph=shacl_graph, advanced=True)

    print(f"Validation conforms: {conforms}")
    print(message)


run_shacl_validation()

# Run the reasoner
#with onto:
    #sync_reasoner(infer_property_values=True)
    #print(list(default_world.inconsistent_classes()))

# Save the ontology
onto.save(file="app\data\ifix-it-kg.owl", format="rdfxml")