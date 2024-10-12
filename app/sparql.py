from rdflib import Graph

g = Graph()
g.parse("app/data/ifix-it-kg.owl", format="xml")


# Find all procedures with more than 6 steps.
query = """
PREFIX owl: <http://www.w3.org/2002/07/owl#>
PREFIX rdf: <http://www.w3.org/1999/02/22-rdf-syntax-ns#>
PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#>
PREFIX onto: <http://cits3005.org/pc-ontology.owl#>

SELECT ?procedure (COUNT(?step) AS ?step_count)
WHERE {
  ?procedure rdf:type onto:Procedure.
  ?step rdf:type onto:Step.
  ?step onto:isPartOfProcedure ?procedure.
}
GROUP BY ?procedure
HAVING (COUNT(?step) > 6)
"""

qres = g.query(query)
for row in qres:
    print(row)


# Find all items that have more than 10 procedures written for them
query = """
PREFIX owl: <http://www.w3.org/2002/07/owl#>
PREFIX rdf: <http://www.w3.org/1999/02/22-rdf-syntax-ns#>
PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#>
PREFIX onto: <http://cits3005.org/pc-ontology.owl#>

SELECT ?item (COUNT(?procedure) AS ?procedure_count)
WHERE {
    ?procedure rdf:type onto:Procedure.
    {
        
        ?procedure onto:isForItem ?item.
    } 
    UNION
    {
        ?pItem rdf:type onto:Item.
        
        ?item onto:isPartOf ?pItem.
        ?procedure onto:isForItem ?pItem.
    }
    UNION
    {
        ?item rdf:type onto:Item.
        
        ?pItem onto:isPartOf ?item.
        ?procedure onto:isForItem ?pItem.
    }
}
GROUP BY ?item
HAVING (COUNT(?procedure) > 10)
"""

qres = g.query(query)
for row in qres:
    print(row)


# Find all procedures that include a tool that is never mentioned in the procedure steps
query = """
PREFIX owl: <http://www.w3.org/2002/07/owl#>
PREFIX rdf: <http://www.w3.org/1999/02/22-rdf-syntax-ns#>
PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#>
PREFIX onto: <http://cits3005.org/pc-ontology.owl#>

SELECT ?procedure ?tool WHERE {
  ?toolbox onto:isForProcedure ?procedure.
  ?toolbox onto:containsTool ?tool.
  FILTER NOT EXISTS {
    ?step onto:usesTool ?tool.
    ?step onto:isPartOfProcedure ?procedure.
  }
}
"""

qres = g.query(query)
for row in qres:
    print(row)


# Flag Potential Hazards in Procedures
query = """
PREFIX owl: <http://www.w3.org/2002/07/owl#>
PREFIX rdf: <http://www.w3.org/1999/02/22-rdf-syntax-ns#>
PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#>
PREFIX onto: <http://cits3005.org/pc-ontology.owl#>

SELECT ?step ?text
WHERE {
    ?step rdf:type onto:Step.
    ?step onto:hasText ?textNode.
    ?textNode rdfs:label ?text .
    FILTER(CONTAINS(LCASE(?text), "careful") ||
        CONTAINS(LCASE(?text), "dangerous"))
}
GROUP BY ?step
"""

qres = g.query(query)
for row in qres:
    print(row)
