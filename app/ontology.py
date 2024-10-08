from owlready2 import *

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
