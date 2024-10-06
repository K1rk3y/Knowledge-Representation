from owlready2 import *
import json


# Create a new ontology
onto = get_ontology("http://cits3005.org/pc-ontology.owl")

with onto:
    # Define classes
    class Item(Thing):
        pass

    class Part(Item):
        pass

    class Procedure(Thing):
        pass

    class Step(Thing):
        pass

    class Tool(Thing):
        pass

    class Image(Thing):
        pass

    class Toolbox(Thing):
        pass

    class Text(Thing):
        pass

    class Hazard(Thing):
        pass

    # Define object properties
    class hasSubclass(Item >> Item, TransitiveProperty):
        pass

    class hasPart(Item >> Part, TransitiveProperty):
        pass

    class isPartOf(Part >> Item, TransitiveProperty):
        inverse_property = hasPart

    class hasStep(Procedure >> Step):
        pass

    class isForItem(Procedure >> Item):
        pass

    class usesTool(Step >> Tool):
        pass

    class hasImage(Step >> Image):
        pass

    class hasText(Step >> Text):
        pass

    class describes(Text >> Step):
        inverse_property = hasText

    class isPartOfProcedure(Step >> Procedure):
        inverse_property = hasStep

    class isUsedInStep(Tool >> Step):
        inverse_property = usesTool

    class isInToolbox(Tool >> Toolbox):
        pass

    class illustratesStep(Image >> Step):
        inverse_property = hasImage

    class containsTool(Toolbox >> Tool):
        inverse_property = isInToolbox

    class isForProcedure(Toolbox >> Procedure):
        pass

    # Define data properties
    class hasOrder(Step >> int):
        pass

    # Define Sub_Procedure class with equivalence
    class Sub_Procedure(Procedure):
        pass

    # Define hasSubProcedure property
    class hasSubProcedure(Procedure >> Procedure):
        pass

    class hasHazard(Step >> Hazard):
        pass



    class Toshiba_Satellite_1805_S177(Item):
        pass

    class Asus_V6800V(Item):
        pass

    class Alienware_M15x(Item):
        pass

    class IBM_ThinkPad_T41(Item):
        pass

    class Sony_Vaio_VGN_S260(Item):
        pass

    class Compaq_Evo_N1000v(Item):
        pass

    class Panasonic_Toughbook_CF_29(Item):
        pass

    class Gateway_SA1(Item):
        pass

    class Acer_Aspire_5100(Item):
        pass

    class Sony_Vaio_PCG_F420(Item):
        pass

    class Dell_Latitude_D620(Item):
        pass

    class IBM_ThinkPad_560z(Item):
        pass

    class Sony_Vaio_PCG_F360(Item):
        pass

    class Dell_Inspiron_1150(Item):
        pass

    class Sony_Vaio_PCG_981L(Item):
        pass

    class Sony_Vaio_PCG_7A2L(Item):
        pass

    class Sony_Vaio_PCG_6J2L(Item):
        pass

    class Dell_Latitude_E6400(Item):
        pass

    class Fujitsu_Siemens_Amilo_Pro(Item):
        pass

    class IBM_ThinkPad_T42(Item):
        pass

    class Acer_Aspire_One_D150(Item):
        pass

    class Toshiba_Satellite_M45(Item):
        pass

    # Define classes for each laptop model with a repair procedure and equivalences
    class Toshiba_Satellite_1805_S177_repair_procedure(Procedure):
        equivalent_to = [Procedure & isForItem.some((Toshiba_Satellite_1805_S177))]

    class Asus_V6800V_repair_procedure(Procedure):
        equivalent_to = [Procedure & isForItem.some((Asus_V6800V))]

    class Alienware_M15x_repair_procedure(Procedure):
        equivalent_to = [Procedure & isForItem.some((Alienware_M15x))]

    class IBM_ThinkPad_T41_repair_procedure(Procedure):
        equivalent_to = [Procedure & isForItem.some((IBM_ThinkPad_T41))]

    class Sony_Vaio_VGN_S260_repair_procedure(Procedure):
        equivalent_to = [Procedure & isForItem.some((Sony_Vaio_VGN_S260))]

    class Compaq_Evo_N1000v_repair_procedure(Procedure):
        equivalent_to = [Procedure & isForItem.some((Compaq_Evo_N1000v))]

    class Panasonic_Toughbook_CF_29_repair_procedure(Procedure):
        equivalent_to = [Procedure & isForItem.some((Panasonic_Toughbook_CF_29))]

    class Gateway_SA1_repair_procedure(Procedure):
        equivalent_to = [Procedure & isForItem.some((Gateway_SA1))]

    class Acer_Aspire_5100_repair_procedure(Procedure):
        equivalent_to = [Procedure & isForItem.some((Acer_Aspire_5100))]

    class Sony_Vaio_PCG_F420_repair_procedure(Procedure):
        equivalent_to = [Procedure & isForItem.some((Sony_Vaio_PCG_F420))]

    class Dell_Latitude_D620_repair_procedure(Procedure):
        equivalent_to = [Procedure & isForItem.some((Dell_Latitude_D620))]

    class IBM_ThinkPad_560z_repair_procedure(Procedure):
        equivalent_to = [Procedure & isForItem.some((IBM_ThinkPad_560z))]

    class Sony_Vaio_PCG_F360_repair_procedure(Procedure):
        equivalent_to = [Procedure & isForItem.some((Sony_Vaio_PCG_F360))]

    class Dell_Inspiron_1150_repair_procedure(Procedure):
        equivalent_to = [Procedure & isForItem.some((Dell_Inspiron_1150))]

    class Sony_Vaio_PCG_981L_repair_procedure(Procedure):
        equivalent_to = [Procedure & isForItem.some((Sony_Vaio_PCG_981L))]

    class Sony_Vaio_PCG_7A2L_repair_procedure(Procedure):
        equivalent_to = [Procedure & isForItem.some((Sony_Vaio_PCG_7A2L))]

    class Sony_Vaio_PCG_6J2L_repair_procedure(Procedure):
        equivalent_to = [Procedure & isForItem.some((Sony_Vaio_PCG_6J2L))]

    class Dell_Latitude_E6400_repair_procedure(Procedure):
        equivalent_to = [Procedure & isForItem.some((Dell_Latitude_E6400))]

    class Fujitsu_Siemens_Amilo_Pro_repair_procedure(Procedure):
        equivalent_to = [Procedure & isForItem.some((Fujitsu_Siemens_Amilo_Pro))]

    class IBM_ThinkPad_T42_repair_procedure(Procedure):
        equivalent_to = [Procedure & isForItem.some((IBM_ThinkPad_T42))]

    class Acer_Aspire_One_D150_repair_procedure(Procedure):
        equivalent_to = [Procedure & isForItem.some((Acer_Aspire_One_D150))]

    class Toshiba_Satellite_M45_repair_procedure(Procedure):
        equivalent_to = [Procedure & isForItem.some((Toshiba_Satellite_M45))]



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


def get_or_create(cls, name):
    cleaned_name = clean_string(name)
    instance = cls(cleaned_name)
    if not instance in cls.instances():
        instance.label = name
        return instance
    return cls(cleaned_name)

# Function to clean and standardize names
def clean_string(input_string):
    return input_string.replace(" ", "_").replace("-", "_")


def create_class(cls, category):
    cls = getattr(onto, clean_string(cls), None)
    if cls:
        # If the class exists, create an instance of it
        return cls(category)  # or cls(category) if you want to pass an argument
    else:
        # Handle the case where the class does not exist
        print(f"Class {cls} does not exist.")
        return None


search_list = ['battery', 'cover', 'screen']

data = selection("app\data\PC.json", 3)
# Create instances and relationships
for item in data:
    # Create Item instance
    item_instance = create_class(item['Category'], item['Category'])
    
    # Create Procedure instance
    procedure_instance = get_or_create(Procedure, f"{item['Title']}_Procedure")
    procedure_instance.isForItem.append(item_instance)
    
    # Create Toolbox instance
    toolbox_instance = get_or_create(Toolbox, f"{item['Title']}_Toolbox")
    toolbox_instance.isForProcedure.append(procedure_instance)

    part_instance = get_or_create(Part, item['Subject'])
    part_instance.isPartOf.append(item_instance)
    
    # Create Tool instances
    for tool in item['Toolbox']:
        tool_instance = get_or_create(Tool, tool['Name'])
        toolbox_instance.containsTool.append(tool_instance)
    
    # Create Step instances
    for step in item['Steps']:
        step_instance = get_or_create(Step, f"Step_{step['StepId']}")
        step_instance.isPartOfProcedure.append(procedure_instance)
        
        text_instance = get_or_create(Text, f"Text_{step['StepId']}")
        text_instance.label = step['Text_raw']
        step_instance.hasText.append(text_instance)

        for part in extract_parts(step['Text_raw'], search_list):
            part_instance = get_or_create(Part, part)
            part_instance.isPartOf.append(item_instance)

        if flag_hazards(step['Text_raw']):
            hazard_instance = get_or_create(Hazard, f"Hazard_{step['StepId']}")
            step_instance.hasHazard.append(hazard_instance)
        
        # Create Image instances
        for image_url in step['Images']:
            image_instance = get_or_create(Image, image_url)
            step_instance.hasImage.append(image_instance)
        
        # Link Tools to Steps
        for tool_name in step['Tools_extracted']:
            if tool_name != "NA":
                tool_instance = get_or_create(Tool, tool_name)
                step_instance.usesTool.append(tool_instance)
    
    # Create Item hierarchy
    for ancestor in item['Ancestors']:
        ancestor_instance = get_or_create(Item, ancestor)
        item_instance.isPartOf.append(ancestor_instance)


# Compute sub-procedure relations
for p1 in onto.Procedure.instances():
    for p2 in onto.Procedure.instances():
        if p1 != p2:
            steps_p1 = set(p1.hasStep)
            steps_p2 = set(p2.hasStep)
            if steps_p2 < steps_p1:
                p2.is_a.append(onto.Sub_Procedure)


# Add rules
with onto:
    # Tool Consistency Rule
    rule = Imp()
    rule.set_as_rule("""
        Step(?s), Procedure(?p), Tool(?t), Toolbox(?tb),
        usesTool(?s, ?t), isPartOfProcedure(?s, ?p), isForProcedure(?tb, ?p)
        ->
        containsTool(?tb, ?t)
    """)

    # Sub-Procedure Consistency Rule (Same Item)
    rule = Imp()
    rule.set_as_rule("""
        Sub_Procedure(?p2), Procedure(?p1), Item(?i),
        hasSubProcedure(?p1, ?p2), isForItem(?p1, ?i), isForItem(?p2, ?i), 
        DifferentFrom(?p1, ?p2)
        ->
        DifferentFrom(?p1, ?p2)
    """)

    # Sub-Procedure Consistency Rule (Part Item)
    rule = Imp()
    rule.set_as_rule("""
        Sub_Procedure(?p2), Procedure(?p1), Item(?i1), Item(?i2),
        hasSubProcedure(?p1, ?p2), isForItem(?p1, ?i1), isForItem(?p2, ?i2), 
        DifferentFrom(?i1, ?i2)
        ->
        hasPart(?i1, ?i2)
    """)


# Run the reasoner
# sync_reasoner()

# Save the ontology
onto.save(file="app\data\ifix-it-ontology.owl", format="rdfxml")
