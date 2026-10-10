from .controller import Edge, Graph, Query


def cases():
    query = Query("researcher", ("supervisor", "education"),
                  (frozenset({"person"}), frozenset({"university"})))
    good = [Edge("researcher", "supervisor", "mentor", "fixture"),
            Edge("mentor", "education", "university", "fixture")]
    types = {"mentor": "person", "university": "university", "a_wrong": "company"}
    return {
        "supported": (Graph(good, types), query, 8),
        "missing": (Graph(good[:1], types), query, 8),
        "contradiction": (Graph(good, types, {("mentor", "education")}), query, 8),
        "recovery": (Graph([Edge("researcher", "supervisor", "a_wrong", "fixture"),
                            Edge("a_wrong", "education", "university", "fixture")] + good, types), query, 8),
        "budget": (Graph(good, types), query, 1),
    }
