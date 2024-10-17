from rdflib import Graph

g = Graph()
g.parse("app/data/ifix-it-kg.owl", format="xml")


# Find all procedures with more than 6 steps.
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

qres = g.query(query)
for row in qres:
    print(row)