"""
OOP Aggregator

Aggregates canonical per-file analysis reports into unified project-level
OOP metrics, including class stats, encapsulation, polymorphism, data
structures, complexity, and a narrative summary.
"""

from typing import List, Dict, Any, Set

# Expected canonical class/file shapes 
# Each canonical report (per file) should be a dict like:
# {
#   "file": "src/..",
#   "module": "com.example",
#   "classes": [
#       {
#           "name": "Foo",
#           "bases": ["Base", "IExample"],
#           "methods": ["Foo","doSomething","toString"],
#           "has_constructor": True,
#           "special_methods": ["toString"],
#           "private_attrs": ["x"],
#           "public_attrs": ["name"]
#       }, ...
#   ],
#   "data_structures": { "counts": {"list":1,"dict":1,"set":0,"tuple":0}, "uses_priority_queue": False, ... },
#   "complexity": {"total_functions": 3, "functions_with_nested_loops": 1, "max_loop_depth": 2},
#   "syntax_ok": True
# }

def aggregate_canonical_reports(canonical_reports: List[Dict[str, Any]], total_files: int = None) -> Dict[str, Any]:
    """
    Turn a list of canonical per-file reports into the full project-level metrics dict
    Args:
        canonical_reports (List[Dict[str, Any]]): List of per-file canonical reports.
        total_files (int, optional): Total number of files analyzed (including syntax errors).
                                     If None, defaults to len(canonical_reports).
    """
    # Flatten classes
    all_classes = []
    for rep in canonical_reports:
        for c in rep.get("classes", []):
            # Derive module and file path for each class for possible disambiguation
            class_copy = dict(c)
            class_copy.setdefault("module", rep.get("module", ""))
            class_copy.setdefault("file_path", rep.get("file", rep.get("file_path", "")))
            all_classes.append(class_copy)

    n_files = total_files if total_files is not None else len(canonical_reports)
    n_classes = len(all_classes)

    # Data structures aggregation (normalize to keys used by original analyzer)
    ds_counts = {
        "list_literals": 0,
        "dict_literals": 0,
        "set_literals": 0,
        "tuple_literals": 0,
        "list_comprehensions": 0,
        "dict_comprehensions": 0,
        "set_comprehensions": 0,
    }
    alg_usage = {
        "uses_defaultdict": False,
        "uses_counter": False,
        "uses_heapq": False,
        "uses_bisect": False,
        "uses_sorted": False,
    }

    # Complexity aggregation
    complexity_stats = {
        "total_functions": 0,
        "functions_with_nested_loops": 0,
        "max_loop_depth": 0,
    }

    # Class-level aggregated stats
    total_methods = 0
    inheritance_classes = 0
    classes_with_init = 0
    dunder_rich = 0
    private_attr_classes = 0

    # Build name by methods mapping for override detection
    methods_by_class: Dict[str, Set[str]] = {}

    for c in all_classes:
        methods = set(c.get("methods", []))
        total_methods += len(methods)
        # has inheritance if bases non-empty and not trivial
        bases = c.get("bases", []) or []
        if bases and not (len(bases) == 1 and bases[0] in {"object", "<expr>", ""}):
            inheritance_classes += 1
        if c.get("has_constructor", False) or c.get("has_init", False):
            classes_with_init += 1
        # special_methods list presence counts as dunder-like richness
        if len(c.get("special_methods", [])) >= 2:
            dunder_rich += 1
        if c.get("private_attrs"):
            private_attr_classes += 1

        methods_by_class.setdefault(c.get("name", "<anon>"), set()).update(methods)

    # Polymorphism detection: override methods present in subclasses
    override_classes = 0
    override_method_count = 0

    for c in all_classes:
        base_method_union = set()
        for base in c.get("bases", []):
            if base in methods_by_class:
                base_method_union |= methods_by_class[base]
        overrides = set(c.get("methods", [])) & base_method_union
        if overrides:
            override_classes += 1
            override_method_count += len(overrides)

    # Complexity & data structures aggregation from canonical reports
    for rep in canonical_reports:
        ds = rep.get("data_structures") or {}
        # counts mapping from canonical schema to analyzer keys
        counts = ds.get("counts", {}) if isinstance(ds.get("counts"), dict) else {}
        for key, target in [("list", "list_literals"), ("dict", "dict_literals"), 
                             ("set", "set_literals"), ("tuple", "tuple_literals")]:
            ds_counts[target] += counts.get(key, 0)

        comps = ds.get("comprehensions") or {}
        for key, target in [("list", "list_comprehensions"), ("dict", "dict_comprehensions"),
                             ("set", "set_comprehensions")]:
            ds_counts[target] += comps.get(key, 0)

        for src, target in [("uses_priority_queue", "uses_heapq"), ("uses_sorted", "uses_sorted"),
                             ("uses_counter_like", "uses_counter"), ("uses_defaultdict_like", "uses_defaultdict")]:
            if ds.get(src):
                alg_usage[target] = True

        cx = rep.get("complexity") or {}
        complexity_stats["total_functions"] += cx.get("total_functions", 0)
        complexity_stats["functions_with_nested_loops"] += cx.get("functions_with_nested_loops", 0)
        complexity_stats["max_loop_depth"] = max(complexity_stats["max_loop_depth"], cx.get("max_loop_depth", 0))

    # compute averages/ratios
    avg_methods = (total_methods / n_classes) if n_classes else 0.0

    total_funcs = complexity_stats["total_functions"]
    nested = complexity_stats["functions_with_nested_loops"]
    nested_ratio = (nested / total_funcs) if total_funcs > 0 else 0.0

    # Score calculation
    richness = min(avg_methods / 5.0, 1.0)
    inheritance_ratio = inheritance_classes / n_classes if n_classes else 0.0
    encapsulation_ratio = private_attr_classes / n_classes if n_classes else 0.0
    polymorphism_ratio = (override_classes / inheritance_classes) if inheritance_classes else 0.0
    dunder_ratio = dunder_rich / n_classes if n_classes else 0.0

    oop_score = (
        0.25 * richness +
        0.20 * inheritance_ratio +
        0.25 * encapsulation_ratio +
        0.25 * polymorphism_ratio +
        0.05 * dunder_ratio
    )
    oop_score = max(0.0, min(1.0, oop_score))
    # textual rating
    if n_classes == 0:
        rating = "none"
        comment = (
            "No classes were found in this project, so OOP "
            "usage appears minimal or absent."
        )
    elif oop_score < 0.3:
        rating = "low"
        comment = (
            "The project shows limited use of object-oriented design. "
            "There are some classes, but inheritance, encapsulation, and polymorphism are either absent or lightly used."
        )
    elif oop_score < 0.6:
        rating = "medium"
        comment = (
            "The project demonstrates moderate OOP usage. Classes and methods "
            "are present, with some inheritance or encapsulation, but there is still room to deepen abstraction and polymorphism."
        )
    else:
        rating = "high"
        comment = (
            "The project exhibits strong object-oriented design: classes are well-used, "
            "encapsulation is present, and inheritance with method overriding provides "
            "clear polymorphic behavior and expressive interfaces."
        )

    metrics = {
        "files_analyzed": n_files,
        "classes": {
            "count": n_classes,
            "avg_methods_per_class": round(avg_methods, 2),
            "with_inheritance": inheritance_classes,
            "with_init": classes_with_init,
        },
        "encapsulation": {
            "classes_with_private_attrs": private_attr_classes,
        },
        "polymorphism": {
            "classes_overriding_base_methods": override_classes,
            "override_method_count": override_method_count,
        },
        "special_methods": {
            "classes_with_multiple_dunders": dunder_rich,
        },
        "data_structures": {
            **ds_counts,
            # include algorithm flags too
            "uses_defaultdict": alg_usage["uses_defaultdict"],
            "uses_counter": alg_usage["uses_counter"],
        },
        "complexity": {
            "total_functions": complexity_stats["total_functions"],
            "functions_with_nested_loops": complexity_stats["functions_with_nested_loops"],
            "nested_loop_ratio": round(nested_ratio, 2),
            "max_loop_depth": complexity_stats["max_loop_depth"],
            "uses_sorted": alg_usage["uses_sorted"],
            "uses_heapq": alg_usage["uses_heapq"],
            "uses_bisect": alg_usage["uses_bisect"],
        },
        "score": {
            "oop_score": round(oop_score, 2),
            "rating": rating,
            "comment": comment,
        },
        "syntax_errors": [],  
    }

    # build narrative summary
    metrics["narrative"] = build_narrative(metrics)
    return metrics


def build_narrative(metrics: Dict[str, Any]) -> Dict[str, str]:
    """
    Build the three-part narrative (oop, data_structures, complexity).
    Returns dict { "oop": "...", "data_structures": "...", "complexity": "..." }
    """
    classes = metrics["classes"]
    encaps = metrics["encapsulation"]
    poly = metrics["polymorphism"]
    special = metrics["special_methods"]
    ds = metrics.get("data_structures", {})
    cx = metrics.get("complexity", {})
    score = metrics["score"]["oop_score"]

    n_classes = classes["count"]
    oop_lines = []

    if n_classes == 0:
        oop_lines.append(
            "No classes were detected in the repository, so the codebase is primarily procedural "
            "and does not demonstrate object-oriented abstraction in this artifact."
        )
    else:
        oop_lines.append(
            f"The project defines {n_classes} class(es) with an average of "
            f"{classes['avg_methods_per_class']} method(s) per class."
        )

        if classes["with_inheritance"] == 0:
            oop_lines.append(
                "None of the classes use inheritance, so the author is not relying on subclassing "
                "for code reuse or specialization in this codebase."
            )
        else:
            oop_lines.append(
                f"{classes['with_inheritance']} class(es) use inheritance, indicating some use "
                "of hierarchical relationships between types."
            )

        if classes["with_init"] == 0:
            oop_lines.append(
                "No classes define their own constructors, which suggests limited custom "
                "initialization or stateful objects in this artifact."
            )

        if encaps["classes_with_private_attrs"] == 0:
            oop_lines.append(
                "There is no evidence of encapsulation via private attributes, "
                "so information hiding is not a major focus here."
            )
        else:
            oop_lines.append(
                f"Encapsulation is present: {encaps['classes_with_private_attrs']} class(es) use "
                "private attributes to hide internal state."
            )

        if poly["classes_overriding_base_methods"] == 0:
            oop_lines.append(
                "None of the classes override methods from their base classes, indicating little "
                "use of polymorphism in this code."
            )
        else:
            oop_lines.append(
                f"{poly['classes_overriding_base_methods']} class(es) override "
                f"{poly['override_method_count']} inherited method(s), which is direct evidence of "
                "polymorphism."
            )

        if special["classes_with_multiple_dunders"] > 0:
            oop_lines.append(
                f"{special['classes_with_multiple_dunders']} class(es) implement multiple "
                "special methods, suggesting more expressive class interfaces."
            )

        if score < 0.3:
            oop_lines.append(
                "Overall, the OOP score is low, so this artifact shows only limited use of "
                "object-oriented design beyond basic class or data-holder definitions."     
            )
        elif score < 0.6:
            oop_lines.append(
                "Overall, the OOP score is moderate, indicating some use of object-oriented ideas but still with room for deeper abstraction and polymorphism."
            )
        else:
            oop_lines.append(
                "The high OOP score indicates strong, deliberate use of object-oriented design in this artifact."
            )

    oop_narrative = " ".join(oop_lines)

    # Data structure narrative
    ds_lines = []
    list_count = ds.get("list_literals", 0)
    dict_count = ds.get("dict_literals", 0)
    set_count = ds.get("set_literals", 0)
    tuple_count = ds.get("tuple_literals", 0)
    list_comps = ds.get("list_comprehensions", 0)
    dict_comps = ds.get("dict_comprehensions", 0)
    set_comps = ds.get("set_comprehensions", 0)
    total_literal_collections = list_count + dict_count + set_count + tuple_count

    if total_literal_collections == 0:
        ds_lines.append(
            "The analysis did not detect any collection literals, so data structure usage "
            "appears minimal in this artifact."
        )
    else:
        ds_lines.append(
            f"The code uses {total_literal_collections} collection literal(s): "
            f"{list_count} list(s), {dict_count} dict(s), {set_count} set(s), "
            f"and {tuple_count} tuple(s)."
        )

        if list_count > 0 and dict_count == 0 and set_count == 0:
            ds_lines.append(
                "Lists are used exclusively for collections, which suggests the author primarily "
                "relies on sequential data rather than hash-based lookups or set semantics."
            )
        elif dict_count > 0 or set_count > 0:
            ds_lines.append(
                "The presence of dictionaries and/or sets indicates some awareness of using hash "
                "maps or sets when appropriate for key-based access or membership tests."
            )

        if list_comps + dict_comps + set_comps > 0:
            ds_lines.append(
                f"The author uses {list_comps} list comprehension(s), {dict_comps} dict "
                f"comprehension(s), and {set_comps} set comprehension(s), which shows familiarity "
                "with concise, functional-style collection construction."
            )

        part_flags = []
        if ds.get("uses_defaultdict", False):
            part_flags.append("defaultdict-like structures")
        if ds.get("uses_counter", False):
            part_flags.append("counter-like structures")
        if part_flags:
            ds_lines.append(
                "Use of " + " and ".join(part_flags) + " suggests the author is comfortable "
                "choosing specialized data structures for counting or grouping tasks."
            )
        else:
            ds_lines.append(
                "No usage of specialized counting/grouping helpers was detected, so the "
                "code stays with more basic built-in structures rather than specialized helpers."
            )

    ds_narrative = " ".join(ds_lines)

    # Complexity narrative
    cx_lines = []
    total_funcs = cx.get("total_functions", 0)
    nested_funcs = cx.get("functions_with_nested_loops", 0)
    nested_ratio = cx.get("nested_loop_ratio", 0.0)
    max_depth = cx.get("max_loop_depth", 0)

    if total_funcs == 0:
        cx_lines.append(
            "No functions were detected for complexity analysis, so we cannot infer much about algorithmic design from this artifact."
        )
    else:
        cx_lines.append(
            f"The analyzer examined {total_funcs} function(s); {nested_funcs} of them contain "
            f"nested loops (nested loop ratio {nested_ratio:.2f}, max depth {max_depth})."
        )

        if nested_funcs == 0:
            cx_lines.append(
                "The absence of nested loops suggests most operations are at most linear in the "
                "size of their inputs, with no obvious O(n²) patterns."
            )
        elif nested_ratio <= 0.25:
            cx_lines.append(
                "Only a small fraction of functions use nested loops, indicating that potentially "
                "quadratic behavior is limited to a few focused areas."
            )
        else:
            cx_lines.append(
                "A substantial fraction of functions use nested loops, which may indicate "
                "performance hot spots or opportunities to reduce quadratic behavior."
            )

        algo_bits = []
        if cx.get("uses_sorted", False):
            algo_bits.append("sorted() / sorting utilities")
        if cx.get("uses_heapq", False):
            algo_bits.append("priority-queue usage (heap)")
        if cx.get("uses_bisect", False):
            algo_bits.append("binary-search utilities")
        if algo_bits:
            cx_lines.append(
                "The use of " + ", ".join(algo_bits) +
                " suggests some awareness of algorithmic tools for more efficient querying or "
                "ordering (e.g., O(n log n) sorting or priority queues)."
            )
        else:
            cx_lines.append(
                "No use of sorting/priority-queue/binary-search utilities was detected, so the code does not rely on "
                "more advanced algorithmic utilities in this artifact."
            )

    cx_narrative = " ".join(cx_lines)

    return {
        "oop": oop_narrative,
        "data_structures": ds_narrative,
        "complexity": cx_narrative,
    }

def pretty_print_oop_report(metrics: dict):
    """Print a formatted OOP analysis report to stdout."""
    print("\n" + "="*60)
    print("        OOP ANALYSIS REPORT")
    print("="*60)

    print(f"\n Files analyzed: {metrics['files_analyzed']}")
    print("\n Class Statistics")
    print("-"*60)
    print(f"• Total classes             : {metrics['classes']['count']}")
    print(f"• Avg methods per class     : {metrics['classes']['avg_methods_per_class']}")
    print(f"• Classes using inheritance : {metrics['classes']['with_inheritance']}")
    print(f"• Classes with __init__     : {metrics['classes']['with_init']}")

    print("\n Encapsulation")
    print("-"*60)
    print(f"• Classes with private attrs: {metrics['encapsulation']['classes_with_private_attrs']}")

    print("\n Polymorphism")
    print("-"*60)
    print(f"• Classes overriding methods: {metrics['polymorphism']['classes_overriding_base_methods']}")
    print(f"• Total overridden methods  : {metrics['polymorphism']['override_method_count']}")

    print("\n Special Methods")
    print("-"*60)
    print(f"• Classes w/ multiple dunders: {metrics['special_methods']['classes_with_multiple_dunders']}")
    
    ds = metrics.get("data_structures", {})
    print("\n Data Structures")
    print("-"*60)
    print(f"• List literals             : {ds.get('list_literals', 0)}")
    print(f"• Dict literals             : {ds.get('dict_literals', 0)}")
    print(f"• Set literals              : {ds.get('set_literals', 0)}")
    print(f"• Tuple literals            : {ds.get('tuple_literals', 0)}")
    print(f"• List comprehensions       : {ds.get('list_comprehensions', 0)}")
    print(f"• Dict comprehensions       : {ds.get('dict_comprehensions', 0)}")
    print(f"• Set comprehensions        : {ds.get('set_comprehensions', 0)}")
    print(f"• Uses collections.defaultdict: {ds.get('uses_defaultdict', False)}")
    print(f"• Uses collections.Counter    : {ds.get('uses_counter', False)}")
    
    cx = metrics.get("complexity", {})
    print("\n  Complexity & Algorithms")
    print("-"*60)
    print(f"• Total functions           : {cx.get('total_functions', 0)}")
    print(f"• Funcs with nested loops   : {cx.get('functions_with_nested_loops', 0)}")
    print(f"• Nested loop ratio         : {cx.get('nested_loop_ratio', 0.0)}")
    print(f"• Max loop depth            : {cx.get('max_loop_depth', 0)}")
    print(f"• Uses sorted()             : {cx.get('uses_sorted', False)}")
    print(f"• Uses heapq                : {cx.get('uses_heapq', False)}")
    print(f"• Uses bisect               : {cx.get('uses_bisect', False)}")

    print("\n OOP Score")
    print("-"*60)
    print(f"• Score   : {metrics['score']['oop_score']}")
    print(f"• Rating  : {metrics['score']['rating'].upper()}")
    print(f"• Comment : {metrics['score']['comment']}")

    if metrics["syntax_errors"]:
        print("\n Syntax Errors")
        print("-"*60)
        for err in metrics["syntax_errors"]:
            print(f"• {err}")
    else:
        print("\n No syntax errors found")

    narrative = metrics.get("narrative", {})
    print("\n Narrative Insights")
    print("-"*60)
    if "oop" in narrative:
        print("\n[OOP]")
        print(narrative["oop"])
    if "data_structures" in narrative:
        print("\n[Data Structures]")
        print(narrative["data_structures"])
    if "complexity" in narrative:
        print("\n[Complexity & Algorithms]")
        print(narrative["complexity"])

    print("\n" + "="*60 + "\n")