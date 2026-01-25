"""
OOP Aggregator

Aggregates canonical per-file analysis reports into unified project-level
OOP metrics, including class stats, encapsulation, polymorphism, data
structures, complexity, and a narrative summary.
"""

from typing import List, Dict, Any, Set, Tuple

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
    """
    if not canonical_reports:
        return aggregate_python_canonical_reports(canonical_reports, total_files)

    language_groups = group_reports_by_language(canonical_reports)
    if len(language_groups) == 1:
        language = next(iter(language_groups))
        handler = LANGUAGE_AGGREGATORS.get(language, aggregate_python_canonical_reports)
        metrics = handler(language_groups[language], total_files)
        if "language" not in metrics:
            metrics["language"] = language
        return metrics

    return aggregate_multi_language_reports(canonical_reports, total_files)

def detect_language(canonical_reports: List[Dict[str, Any]]) -> str:
    """Detect language from canonical reports"""
    if not canonical_reports:
        return "Python"  # default

    languages = {detect_language_for_report(rep) for rep in canonical_reports}
    languages.discard("Unknown")
    if not languages:
        return "Python"
    if len(languages) == 1:
        return next(iter(languages))
    return "Multi"

def detect_language_for_report(report: Dict[str, Any]) -> str:
    """Detect language for a single canonical report."""
    explicit = report.get("language")
    if explicit:
        return explicit
    if "c_spec" in report:
        return "C"
    if "cpp_spec" in report:
        return "C++"

    file = report.get("file", "") or report.get("file_path", "")
    file = file.lower()
    if file.endswith((".py",)):
        return "Python"
    if file.endswith((".java",)):
        return "Java"
    if file.endswith((".js", ".jsx", ".mjs")):
        return "JavaScript"
    if file.endswith((".c",)):
        return "C"
    if file.endswith((".cpp", ".cc", ".cxx", ".hpp", ".hh", ".hxx")):
        return "C++"
    if file.endswith((".cs",)):
        return "C#"
    if file.endswith((".h",)):
        return "C"

    return "Unknown"

def group_reports_by_language(canonical_reports: List[Dict[str, Any]]) -> Dict[str, List[Dict[str, Any]]]:
    """
    Group canonical reports by detected language.

    Args:
        canonical_reports: Canonical per-file reports to group.

    Returns:
        Mapping of language name to list of reports for that language.
    """
    groups: Dict[str, List[Dict[str, Any]]] = {}
    for rep in canonical_reports:
        lang = detect_language_for_report(rep)
        groups.setdefault(lang, []).append(rep)
    if "Unknown" in groups:
        groups.setdefault("Python", []).extend(groups.pop("Unknown"))
    return groups

def _merge_numeric_or_bool(target: Dict[str, Any], src: Dict[str, Any]) -> None:
    """
    Merge numeric counters (sum) and boolean flags (OR) into target.

    Args:
        target: Destination dictionary to update in-place.
        src: Source dictionary with numeric/boolean values.

    Returns:
        None. Mutates target in-place.
    """
    for key, value in src.items():
        if isinstance(value, bool):
            target[key] = target.get(key, False) or value
        elif isinstance(value, (int, float)):
            target[key] = target.get(key, 0) + value

def _score_rating_comment(n_classes: int, oop_score: float) -> Tuple[str, str]:
    """
    Return rating and comment text based on class count and OOP score.

    Args:
        n_classes: Total number of classes detected.
        oop_score: Normalized OOP score in [0, 1].

    Returns:
        Tuple of (rating, comment).
    """
    if n_classes == 0:
        return (
            "none",
            "No classes were found in this project, so OOP usage appears minimal or absent.",
        )
    if oop_score < 0.3:
        return (
            "low",
            "The project shows limited use of object-oriented design. There are some classes, "
            "but inheritance, encapsulation, and polymorphism are either absent or lightly used.",
        )
    if oop_score < 0.6:
        return (
            "medium",
            "The project demonstrates moderate OOP usage. Classes and methods are present, with "
            "some inheritance or encapsulation, but there is still room to deepen abstraction "
            "and polymorphism.",
        )
    return (
        "high",
        "The project exhibits strong object-oriented design: classes are well-used, encapsulation "
        "is present, and inheritance with method overriding provides clear polymorphic behavior "
        "and expressive interfaces.",
    )

def aggregate_multi_language_reports(
    canonical_reports: List[Dict[str, Any]], total_files: int = None
) -> Dict[str, Any]:
    """
    Aggregate a mixed set of canonical reports into a single multi-language report.

    Args:
        canonical_reports: Canonical per-file reports across languages.
        total_files: Optional total number of analyzed files.

    Returns:
        Combined multi-language metrics dictionary.
    """
    language_groups = group_reports_by_language(canonical_reports)
    language_metrics: Dict[str, Dict[str, Any]] = {}

    for language, reports in language_groups.items():
        handler = LANGUAGE_AGGREGATORS.get(language, aggregate_python_canonical_reports)
        metrics = handler(reports, total_files=len(reports))
        metrics["language"] = language
        language_metrics[language] = metrics

    return combine_language_metrics(language_metrics, total_files)

def combine_language_metrics(
    language_metrics: Dict[str, Dict[str, Any]], total_files: int = None
) -> Dict[str, Any]:
    """
    Combine multiple per-language metric dicts into a single report.

    Args:
        language_metrics: Mapping of language name to per-language metrics.
        total_files: Optional total number of analyzed files.

    Returns:
        Combined multi-language metrics dictionary.
    """
    total_files_count = total_files if total_files is not None else sum(
        m.get("files_analyzed", 0) for m in language_metrics.values()
    )

    total_classes = sum(m.get("classes", {}).get("count", 0) for m in language_metrics.values())
    total_methods = 0.0
    inheritance_classes = 0
    classes_with_init = 0 
    private_attr_classes = 0
    override_classes = 0
    override_method_count = 0
    dunder_rich = 0

    combined_ds: Dict[str, Any] = {}
    combined_cx: Dict[str, Any] = {
        "total_functions": 0,
        "functions_with_nested_loops": 0,
        "max_loop_depth": 0,
    }
    combined_cx_extra: Dict[str, Any] = {}

    combined_syntax_errors: List[str] = []
    total_score_weight = 0.0
    weighted_score_sum = 0.0

    for metrics in language_metrics.values():
        classes = metrics.get("classes", {})
        count = classes.get("count", 0)
        avg_methods = classes.get("avg_methods_per_class", 0)
        total_methods += avg_methods * count
        inheritance_classes += classes.get("with_inheritance", 0)
        classes_with_init += classes.get("with_init", 0)

        encaps = metrics.get("encapsulation", {})
        private_attr_classes += encaps.get("classes_with_private_attrs", 0)

        poly = metrics.get("polymorphism", {})
        override_classes += poly.get("classes_overriding_base_methods", 0)
        override_method_count += poly.get("override_method_count", 0)

        special = metrics.get("special_methods", {})
        dunder_rich += special.get("classes_with_multiple_dunders", 0)

        _merge_numeric_or_bool(combined_ds, metrics.get("data_structures", {}))

        cx = metrics.get("complexity", {})
        combined_cx["total_functions"] += cx.get("total_functions", 0)
        combined_cx["functions_with_nested_loops"] += cx.get("functions_with_nested_loops", 0)
        combined_cx["max_loop_depth"] = max(
            combined_cx["max_loop_depth"], cx.get("max_loop_depth", 0)
        )
        for key, value in cx.items():
            if key in {"total_functions", "functions_with_nested_loops", "max_loop_depth", "nested_loop_ratio"}:
                continue
            if isinstance(value, bool):
                combined_cx_extra[key] = combined_cx_extra.get(key, False) or value
            elif isinstance(value, (int, float)):
                combined_cx_extra[key] = combined_cx_extra.get(key, 0) + value

        combined_syntax_errors.extend(metrics.get("syntax_errors", []) or [])

        weight = metrics.get("files_analyzed", 0) or 0
        if weight:
            total_score_weight += weight
            weighted_score_sum += weight * metrics.get("score", {}).get("oop_score", 0)

    avg_methods_per_class = (total_methods / total_classes) if total_classes else 0.0
    total_funcs = combined_cx["total_functions"]
    nested = combined_cx["functions_with_nested_loops"]
    nested_ratio = (nested / total_funcs) if total_funcs else 0.0

    oop_score = (weighted_score_sum / total_score_weight) if total_score_weight else 0.0
    oop_score = max(0.0, min(1.0, oop_score))
    rating, comment = _score_rating_comment(total_classes, oop_score)

    metrics = {
        "language": "Multi",
        "files_analyzed": total_files_count,
        "languages": language_metrics,
        "classes": {
            "count": total_classes,
            "avg_methods_per_class": round(avg_methods_per_class, 2),
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
        "data_structures": combined_ds,
        "complexity": {
            "total_functions": combined_cx["total_functions"],
            "functions_with_nested_loops": combined_cx["functions_with_nested_loops"],
            "nested_loop_ratio": round(nested_ratio, 2),
            "max_loop_depth": combined_cx["max_loop_depth"],
            **combined_cx_extra,
        },
        "score": {
            "oop_score": round(oop_score, 2),
            "rating": rating,
            "comment": comment,
        },
        "syntax_errors": combined_syntax_errors,
    }

    metrics["narrative"] = build_multi_language_narrative(metrics)
    return metrics

def build_multi_language_narrative(metrics: Dict[str, Any]) -> Dict[str, str]:
    """
    Build a combined narrative for multi-language metrics.

    Args:
        metrics: Combined metrics dictionary with per-language breakdowns.

    Returns:
        Dictionary containing narrative strings for OOP, data structures, and complexity.
    """
    base = build_narrative(metrics)
    languages = sorted((metrics.get("languages") or {}).keys())
    if languages:
        prefix = (
            f"This report aggregates OOP metrics across {len(languages)} language(s): "
            f"{', '.join(languages)}."
        )
        base["oop"] = prefix + " " + base.get("oop", "")

    ds = metrics.get("data_structures", {})
    numeric_ds_total = sum(v for v in ds.values() if isinstance(v, (int, float)))
    if numeric_ds_total == 0:
        base["data_structures"] = (
            "The analysis did not detect notable data-structure usage across the combined "
            "languages in this artifact."
        )
    else:
        base["data_structures"] = (
            f"The analysis detected {numeric_ds_total} data-structure indicator(s) across the "
            "combined languages. See the per-language breakdown for details."
        )

    return base

def aggregate_python_canonical_reports(canonical_reports: List[Dict[str, Any]], total_files: int = None) -> Dict[str, Any]:
    """
    Turn a list of canonical per-file reports into the full project-level metrics dict
    Args:
        canonical_reports (List[Dict[str, Any]]): List of per-file canonical reports.
        total_files (int, optional): Total number of files analyzed (including syntax errors).
                                     If None, defaults to len(canonical_reports).
        total_files (int, optional): Total number of files analyzed (including syntax errors). If None, defaults to len(canonical_reports).
                                     
    Returns:
        Dict[str, Any]: A dictionary containing aggregated project-level object-oriented
        metrics, complexity statistics, data structure usage, and an overall OOP score.
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

def aggregate_c_reports(canonical_reports: List[Dict[str, Any]], total_files: int = None) -> Dict[str, Any]:
    """Aggregate C-specific reports"""
    
    # Flatten structs (C calls them "classes" for compatibility)
    all_classes = []
    for rep in canonical_reports:
        for c in rep.get("classes", []):
            class_copy = dict(c)
            class_copy.setdefault("module", rep.get("module", ""))
            class_copy.setdefault("file_path", rep.get("file", rep.get("file_path", "")))
            all_classes.append(class_copy)

    n_files = total_files if total_files is not None else len(canonical_reports)
    n_classes = len(all_classes)

    # C-specific data structures
    ds_counts = {
        "arrays": 0,
        "hash_tables": 0,
        "linked_lists": 0,
        "trees": 0,
        "queues": 0,
        "stacks": 0,
        "dynamic_memory": 0,
        "pointer_arrays": 0,
    }
    alg_usage = {
        "uses_qsort": False,
        "uses_bsearch": False,
    }

    # C-specific metrics
    c_specific = {
        "opaque_pointers": 0,
        "vtable_structs": 0,
        "constructor_functions": 0,
        "destructor_functions": 0,
    }

    # Complexity aggregation (same for all languages)
    complexity_stats = {
        "total_functions": 0,
        "functions_with_nested_loops": 0,
        "max_loop_depth": 0,
    }

    # Struct-level aggregated stats
    total_methods = 0
    inheritance_classes = 0
    classes_with_init = 0
    vtable_structs = 0
    private_attr_classes = 0

    methods_by_class: Dict[str, Set[str]] = {}

    for c in all_classes:
        methods = set(c.get("methods", []))
        total_methods += len(methods)
        
        bases = c.get("bases", []) or []
        if bases and not (len(bases) == 1 and bases[0] in {"object", "<expr>", ""}):
            inheritance_classes += 1
        
        if c.get("has_constructor", False) or c.get("has_init", False):
            classes_with_init += 1
        
        if c.get("is_vtable", False):
            vtable_structs += 1
        
        if len(c.get("special_methods", [])) >= 2:
            pass  # C doesn't have dunders
        
        if c.get("private_attrs"):
            private_attr_classes += 1

        methods_by_class.setdefault(c.get("name", "<anon>"), set()).update(methods)

    # Polymorphism detection
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

    # Aggregate data from reports
    for rep in canonical_reports:
        ds = rep.get("data_structures") or {}
        
        # Aggregate C data structures
        for key in ["arrays", "hash_tables", "linked_lists", "trees", "queues", "stacks", "dynamic_memory", "pointer_arrays"]:
            ds_counts[key] += ds.get(key, 0)
        
        # Aggregate algorithm usage
        if ds.get("uses_qsort"):
            alg_usage["uses_qsort"] = True
        if ds.get("uses_bsearch"):
            alg_usage["uses_bsearch"] = True

        # Aggregate C-specific metrics
        c_spec = rep.get("c_spec") or {}
        c_specific["opaque_pointers"] += c_spec.get("opaque_pointers", 0)
        c_specific["vtable_structs"] += c_spec.get("vtable_structs", 0)
        c_specific["constructor_functions"] += c_spec.get("constructor_functions", 0)
        c_specific["destructor_functions"] += c_spec.get("destructor_functions", 0)

        # Complexity
        cx = rep.get("complexity") or {}
        complexity_stats["total_functions"] += cx.get("total_functions", 0)
        complexity_stats["functions_with_nested_loops"] += cx.get("functions_with_nested_loops", 0)
        complexity_stats["max_loop_depth"] = max(complexity_stats["max_loop_depth"], cx.get("max_loop_depth", 0))

    # Compute ratios
    avg_methods = (total_methods / n_classes) if n_classes else 0.0
    total_funcs = complexity_stats["total_functions"]
    nested = complexity_stats["functions_with_nested_loops"]
    nested_ratio = (nested / total_funcs) if total_funcs > 0 else 0.0

    # Score calculation (adapted for C)
    richness = min(avg_methods / 5.0, 1.0)
    inheritance_ratio = inheritance_classes / n_classes if n_classes else 0.0
    encapsulation_ratio = min(c_specific["opaque_pointers"] / max(n_classes, 1), 1.0)  # Use opaque pointers for C
    polymorphism_ratio = min(vtable_structs / max(n_classes, 1), 1.0)  # Use vtables for C polymorphism
    lifecycle_ratio = min((c_specific["constructor_functions"] + c_specific["destructor_functions"]) / max(total_funcs, 1), 1.0)

    oop_score = (
        0.20 * richness +
        0.20 * inheritance_ratio +
        0.25 * encapsulation_ratio +
        0.25 * polymorphism_ratio +
        0.10 * lifecycle_ratio
    )
    oop_score = max(0.0, min(1.0, oop_score))

    # Rating
    if n_classes == 0:
        rating = "none"
        comment = "No structs were found in this project, so OOP-like patterns appear minimal or absent."
    elif oop_score < 0.3:
        rating = "low"
        comment = "The project shows limited use of object-oriented patterns. There are some structs, but encapsulation and polymorphism are minimal."
    elif oop_score < 0.6:
        rating = "medium"
        comment = "The project demonstrates moderate OOP-like design with structs, function pointers, and some encapsulation patterns."
    else:
        rating = "high"
        comment = "The project exhibits strong object-oriented design patterns: vtables, opaque pointers, and clear lifecycle management."

    metrics = {
        "language": "C",
        "files_analyzed": n_files,
        "classes": {
            "count": n_classes,
            "avg_methods_per_class": round(avg_methods, 2),
            "with_inheritance": inheritance_classes,
            "with_init": classes_with_init,
        },
        "encapsulation": {
            "classes_with_private_attrs": 0,  # Add this - C doesn't really have this
            "opaque_pointers": c_specific["opaque_pointers"],  # C-specific
        },
        "polymorphism": {
            "classes_overriding_base_methods": override_classes,
            "override_method_count": override_method_count,
            "vtable_structs": c_specific["vtable_structs"],  # C-specific
        },
        "special_methods": {
            "classes_with_multiple_dunders": 0,  # Add this - C doesn't have dunders
        },
        "lifecycle": {  # C-specific section
            "constructor_functions": c_specific["constructor_functions"],
            "destructor_functions": c_specific["destructor_functions"],
        },
        "data_structures": {
            **ds_counts,
            **alg_usage,
        },
        "complexity": {
            "total_functions": complexity_stats["total_functions"],
            "functions_with_nested_loops": complexity_stats["functions_with_nested_loops"],
            "nested_loop_ratio": round(nested_ratio, 2),
            "max_loop_depth": complexity_stats["max_loop_depth"],
            "uses_qsort": alg_usage["uses_qsort"],
            "uses_bsearch": alg_usage["uses_bsearch"],
        },
        "score": {
            "oop_score": round(oop_score, 2),
            "rating": rating,
            "comment": comment,
        },
        "syntax_errors": [],
    }

    metrics["narrative"] = build_c_narrative(metrics)
    return metrics

def aggregate_cpp_reports(canonical_reports: List[Dict[str, Any]], total_files: int = None) -> Dict[str, Any]:
    """
    Aggregate C++ reports into project-level metrics.

    Args:
        canonical_reports: Canonical per-file reports for C++ sources.
        total_files: Optional total number of analyzed files.

    Returns:
        Aggregated C++ metrics dictionary.
    """
    metrics = aggregate_c_reports(canonical_reports, total_files)
    metrics["language"] = "C++"

    cpp_spec = {
        "template_classes": 0,
        "namespaces": 0,
        "abstract_classes": 0,
        "smart_pointers": 0,
        "raii_classes": 0,
        "operator_overloads": 0,
    }
    for rep in canonical_reports:
        spec = rep.get("cpp_spec") or {}
        for key in cpp_spec:
            cpp_spec[key] += spec.get(key, 0)

    metrics["cpp_spec"] = cpp_spec
    metrics["narrative"] = build_cpp_narrative(metrics)
    return metrics

def aggregate_csharp_reports(canonical_reports: List[Dict[str, Any]], total_files: int = None) -> Dict[str, Any]:
    """
    Aggregate C# reports into project-level metrics.

    Args:
        canonical_reports: Canonical per-file reports for C# sources.
        total_files: Optional total number of analyzed files.

    Returns:
        Aggregated C# metrics dictionary.
    """
    metrics = aggregate_python_canonical_reports(canonical_reports, total_files)
    metrics["language"] = "C#"
    metrics["narrative"] = build_csharp_narrative(metrics)
    return metrics

def build_narrative(metrics: Dict[str, Any]) -> Dict[str, str]:
    """
    Build the three-part narrative (oop, data_structures, complexity).

    Args:
        metrics: Dictionary containing aggregated project metrics used to generate narrative summaries.

    Returns:
        Dict[str, str]: A dictionary containing narrative summaries for object-oriented
            design, data structure usage, and algorithmic complexity.
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

# C narrative
def build_c_narrative(metrics: Dict[str, Any]) -> Dict[str, str]:
    """
    Build narrative for C code analysis.

    Args:
        metrics: Aggregated C metrics dictionary.

    Returns:
        Dictionary containing narrative strings for OOP, data structures, and complexity.
    """
    classes = metrics["classes"]
    encaps = metrics["encapsulation"]
    poly = metrics["polymorphism"]
    lifecycle = metrics["lifecycle"]
    ds = metrics.get("data_structures", {})
    cx = metrics.get("complexity", {})

    n_classes = classes["count"]
    oop_lines = []

    if n_classes == 0:
        oop_lines.append(
            "No structs were detected, so the codebase is primarily procedural."
        )
    else:
        oop_lines.append(
            f"The project defines {n_classes} struct(s) with an average of "
            f"{classes['avg_methods_per_class']} function pointer(s) per struct."
        )

        if classes["with_inheritance"] == 0:
            oop_lines.append(
                "No structs use inheritance patterns (base struct as first member)."
            )
        else:
            oop_lines.append(
                f"{classes['with_inheritance']} struct(s) use inheritance via composition."
            )

        if encaps["opaque_pointers"] > 0:
            oop_lines.append(
                f"Encapsulation is present: {encaps['opaque_pointers']} opaque pointer(s) hide implementation details."
            )
        else:
            oop_lines.append("No opaque pointers detected, so encapsulation is minimal.")

        if poly["vtable_structs"] > 0:
            oop_lines.append(
                f"{poly['vtable_structs']} vtable struct(s) provide polymorphic behavior through function pointers."
            )
        else:
            oop_lines.append("No vtable patterns detected, indicating limited polymorphism.")

        if lifecycle["constructor_functions"] > 0 or lifecycle["destructor_functions"] > 0:
            oop_lines.append(
                f"Lifecycle management: {lifecycle['constructor_functions']} constructor(s) and "
                f"{lifecycle['destructor_functions']} destructor(s) manage object creation/cleanup."
            )

    oop_narrative = " ".join(oop_lines)

    # Data structures narrative for C
    ds_lines = []
    arrays = ds.get("arrays", 0)
    hash_tables = ds.get("hash_tables", 0)
    dynamic_mem = ds.get("dynamic_memory", 0)

    if arrays == 0 and hash_tables == 0:
        ds_lines.append("Minimal data structure usage detected.")
    else:
        ds_lines.append(
            f"The code uses {arrays} array(s) and {hash_tables} hash table(s)."
        )
        if dynamic_mem > 0:
            ds_lines.append(
                f"Dynamic memory allocation appears {dynamic_mem} time(s), indicating runtime-sized structures."
            )

    ds_narrative = " ".join(ds_lines)

    # Complexity narrative
    cx_lines = []
    total_funcs = cx.get("total_functions", 0)
    nested_funcs = cx.get("functions_with_nested_loops", 0)

    if total_funcs > 0:
        cx_lines.append(
            f"Analyzed {total_funcs} function(s); {nested_funcs} contain nested loops."
        )
        
        if cx.get("uses_qsort"):
            cx_lines.append("Uses qsort() for sorting.")
        if cx.get("uses_bsearch"):
            cx_lines.append("Uses bsearch() for binary search.")

    cx_narrative = " ".join(cx_lines)

    return {
        "oop": oop_narrative,
        "data_structures": ds_narrative,
        "complexity": cx_narrative,
    }

def build_cpp_narrative(metrics: Dict[str, Any]) -> Dict[str, str]:
    """
    Build narrative for C++ code analysis.

    Args:
        metrics: Aggregated C++ metrics dictionary.

    Returns:
        Dictionary containing narrative strings for OOP, data structures, and complexity.
    """
    classes = metrics["classes"]
    encaps = metrics["encapsulation"]
    poly = metrics["polymorphism"]
    ds = metrics.get("data_structures", {})
    cx = metrics.get("complexity", {})

    n_classes = classes["count"]
    oop_lines = []

    if n_classes == 0:
        oop_lines.append("No classes were detected, so the codebase appears primarily procedural.")
    else:
        oop_lines.append(
            f"The project defines {n_classes} class(es) with an average of "
            f"{classes['avg_methods_per_class']} method(s) per class."
        )

        if classes["with_inheritance"] == 0:
            oop_lines.append("No classes use inheritance, so subclassing is not a primary pattern here.")
        else:
            oop_lines.append(
                f"{classes['with_inheritance']} class(es) use inheritance, indicating some hierarchy usage."
            )

        if encaps["classes_with_private_attrs"] == 0:
            oop_lines.append("No private attributes were detected, so encapsulation is limited.")
        else:
            oop_lines.append(
                f"Encapsulation is present: {encaps['classes_with_private_attrs']} class(es) use private attributes."
            )

        if poly["classes_overriding_base_methods"] == 0:
            oop_lines.append("No method overrides were detected, indicating limited polymorphism.")
        else:
            oop_lines.append(
                f"{poly['classes_overriding_base_methods']} class(es) override "
                f"{poly['override_method_count']} inherited method(s), showing polymorphism."
            )

    oop_narrative = " ".join(oop_lines)

    ds_lines = []
    arrays = ds.get("arrays", 0)
    hash_tables = ds.get("hash_tables", 0)
    linked_lists = ds.get("linked_lists", 0)
    trees = ds.get("trees", 0)
    queues = ds.get("queues", 0)
    stacks = ds.get("stacks", 0)
    dynamic_mem = ds.get("dynamic_memory", 0)

    total_structs = arrays + hash_tables + linked_lists + trees + queues + stacks
    if total_structs == 0:
        ds_lines.append("Minimal container usage detected in the C++ code.")
    else:
        ds_lines.append(
            f"The code uses {total_structs} container instance(s): "
            f"{arrays} array/vector-like, {hash_tables} hash table(s), {linked_lists} list(s), "
            f"{trees} tree/set(s), {queues} queue(s), and {stacks} stack(s)."
        )
        if dynamic_mem > 0:
            ds_lines.append(
                f"Dynamic allocation appears {dynamic_mem} time(s), indicating heap-managed structures."
            )

    ds_narrative = " ".join(ds_lines)

    cx_lines = []
    total_funcs = cx.get("total_functions", 0)
    nested_funcs = cx.get("functions_with_nested_loops", 0)
    max_depth = cx.get("max_loop_depth", 0)

    if total_funcs == 0:
        cx_lines.append("No functions were detected for complexity analysis.")
    else:
        cx_lines.append(
            f"Analyzed {total_funcs} function(s); {nested_funcs} contain nested loops "
            f"(max depth {max_depth})."
        )

    cx_narrative = " ".join(cx_lines)

    return {
        "oop": oop_narrative,
        "data_structures": ds_narrative,
        "complexity": cx_narrative,
    }

def build_csharp_narrative(metrics: Dict[str, Any]) -> Dict[str, str]:
    """
    Build narrative for C# code analysis.

    Args:
        metrics: Aggregated C# metrics dictionary.

    Returns:
        Dictionary containing narrative strings for OOP, data structures, and complexity.
    """
    base = build_narrative(metrics)
    ds = metrics.get("data_structures", {})
    arrays = ds.get("arrays", 0)
    lists = ds.get("lists", 0)
    dictionaries = ds.get("dictionaries", 0)
    queues = ds.get("queues", 0)
    stacks = ds.get("stacks", 0)
    hash_sets = ds.get("hash_sets", 0)
    total_structs = arrays + lists + dictionaries + queues + stacks + hash_sets

    if total_structs == 0:
        base["data_structures"] = (
            "The analysis did not detect common collection types in this C# artifact."
        )
    else:
        base["data_structures"] = (
            f"The code uses {total_structs} collection instance(s): {arrays} array(s), "
            f"{lists} list(s), {dictionaries} dictionary(ies), {queues} queue(s), "
            f"{stacks} stack(s), and {hash_sets} hash set(s)."
        )

    return base

LANGUAGE_AGGREGATORS = {
    "Python": aggregate_python_canonical_reports,
    "Java": aggregate_python_canonical_reports,
    "JavaScript": aggregate_python_canonical_reports,
    "C": aggregate_c_reports,
    "C++": aggregate_cpp_reports,
    "C#": aggregate_csharp_reports,
}

def pretty_print_oop_report(metrics: dict):
    """Print a formatted OOP analysis report to stdout."""

    language = metrics.get("language", "Python")
    if language == "C":
        print_c_report(metrics)
        return

    print("\n" + "="*60)
    print("        OOP ANALYSIS REPORT")
    print("="*60)

    print(f"\n Files analyzed: {metrics['files_analyzed']}")
    print("\n Class Statistics")
    print("-"*60)
    print(f"• Total classes             : {metrics['classes']['count']}")
    print(f"• Avg methods per class     : {metrics['classes']['avg_methods_per_class']}")
    print(f"• Classes using inheritance : {metrics['classes']['with_inheritance']}")
    print(f"• Classes with constructor  : {metrics['classes']['with_init']}")

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

# C specific printing
def print_c_report(metrics: dict):
    """Print C-specific report"""
    print("\n Struct Statistics")
    print("-"*60)
    print(f"• Total structs             : {metrics['classes']['count']}")
    print(f"• Avg func ptrs per struct  : {metrics['classes']['avg_methods_per_class']}")
    print(f"• Structs with inheritance  : {metrics['classes']['with_inheritance']}")
    print(f"• Structs with constructor  : {metrics['classes']['with_init']}")

    print("\n Encapsulation")
    print("-"*60)
    print(f"• Opaque pointers           : {metrics['encapsulation']['opaque_pointers']}")

    print("\n Polymorphism")
    print("-"*60)
    print(f"• Vtable structs            : {metrics['polymorphism']['vtable_structs']}")

    print("\n Lifecycle Management")
    print("-"*60)
    print(f"• Constructor functions     : {metrics['lifecycle']['constructor_functions']}")
    print(f"• Destructor functions      : {metrics['lifecycle']['destructor_functions']}")
    
    ds = metrics.get("data_structures", {})
    print("\n Data Structures")
    print("-"*60)
    print(f"• Arrays                    : {ds.get('arrays', 0)}")
    print(f"• Hash tables               : {ds.get('hash_tables', 0)}")
    print(f"• Dynamic memory allocs     : {ds.get('dynamic_memory', 0)}")
    
    cx = metrics.get("complexity", {})
    print("\n Complexity & Algorithms")
    print("-"*60)
    print(f"• Total functions           : {cx.get('total_functions', 0)}")
    print(f"• Funcs with nested loops   : {cx.get('functions_with_nested_loops', 0)}")
    print(f"• Max loop depth            : {cx.get('max_loop_depth', 0)}")
    print(f"• Uses qsort()              : {cx.get('uses_qsort', False)}")
    print(f"• Uses bsearch()            : {cx.get('uses_bsearch', False)}")

    print("\n OOP-Like Pattern Score")
    print("-"*60)
    print(f"• Score   : {metrics['score']['oop_score']}")
    print(f"• Rating  : {metrics['score']['rating'].upper()}")
    print(f"• Comment : {metrics['score']['comment']}")

    # Narrative
    narrative = metrics.get("narrative", {})
    print("\n Narrative Insights")
    print("-"*60)
    if "oop" in narrative:
        print("\n[OOP-Like Patterns]")
        print(narrative["oop"])
    if "data_structures" in narrative:
        print("\n[Data Structures]")
        print(narrative["data_structures"])
    if "complexity" in narrative:
        print("\n[Complexity]")
        print(narrative["complexity"])

    print("\n" + "="*60 + "\n")
