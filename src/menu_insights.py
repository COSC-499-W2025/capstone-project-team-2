"""
Menu for browsing stored project insights: chronology, skills, rankings, and summaries.

Provides an interactive CLI loop that:
- Lists projects chronologically with stack and summaries
- Shows skill timelines with optional filtering
- Ranks projects via composite scoring (contrib + recency + skills)
- Surfaces top-ranked summaries with rationale

Kept separate from menus.py to keep navigation wiring lean.
"""

from pathlib import Path

from src.project_insights import (
    list_project_insights,
    list_skill_history,
    rank_projects_by_contribution,
    summaries_for_top_ranked_projects,
)
from src.insight_helpers import parse_date, filter_insights, compute_composite_score

def project_insights_menu(ctx) -> None:
    """
    View stored project insights: chronological projects, skill history, rankings, and top summaries.

    Uses the JSON log at User_config_files/project_insights.json to present:
      - Chronological projects (oldest to newest) with type and stack
      - Chronological skills exercised per project
      - Contribution-based ranking (optionally filtered by contributor)
      - Top-ranked project summaries with scores
    """
    storage_path = Path(ctx.legacy_save_dir) / "project_insights.json"

    while True:
        print("\n=== Project Insights ===")
        print("1) Chronological list of projects")
        print("2) Chronological list of skills")
        print("3) Rank projects by contribution")
        print("4) Summaries for top-ranked projects")
        print("0) Exit to Main Menu")

        choice = input("Select an option: ").strip()

        try:
            if choice == "1":
                language = input("Filter by language (optional): ").strip() or None
                skill = input("Filter by skill (optional): ").strip() or None
                since_str = input("Only include analyses since (YYYY-MM-DD, optional): ").strip() or None
                since_dt = parse_date(since_str)

                projects = list_project_insights(storage_path=storage_path)
                projects = filter_insights(
                    projects,
                    language=language,
                    skill=skill,
                    since=since_dt,
                )

                if not projects:
                    print("[INFO] No insights recorded yet.")
                else:
                    print("\nProjects (oldest → newest):\n")
                    for i, p in enumerate(projects, start=1):
                        langs = ", ".join(p.languages) or "—"
                        frws = ", ".join(p.frameworks) or "—"
                        summary = p.summary or "—"
                        print(
                            f"{i}) {p.project_name} | analyzed_at={p.analyzed_at} | "
                            f"type={p.project_type} ({p.detection_mode}) | "
                            f"langs={langs} | frameworks={frws}\n"
                            f"    summary: {summary}"
                        )
                input("\nPress Enter to continue...")

            elif choice == "2":
                skill = input("Filter by skill (optional): ").strip() or None
                since_str = input("Only include analyses since (YYYY-MM-DD, optional): ").strip() or None
                since_dt = parse_date(since_str)

                history = list_skill_history(storage_path=storage_path)
                if since_dt or skill:
                    filtered = []
                    for entry in history:
                        when = parse_date(entry.get("analyzed_at"))
                        if since_dt and when and when < since_dt:
                            continue
                        if skill and all(skill.lower() != s.lower() for s in entry.get("skills", [])):
                            continue
                        filtered.append(entry)
                    history = filtered

                if not history:
                    print("[INFO] No insights recorded yet.")
                else:
                    print("\nSkills (chronological):\n")
                    for entry in history:
                        skills = ", ".join(entry.get("skills", [])) or "—"
                        print(
                            f"- {entry.get('project_name', 'unknown')} "
                            f"@ {entry.get('analyzed_at', 'unknown')} "
                            f"| skills ({entry.get('skill_count', 0)}): {skills}"
                        )
                input("\nPress Enter to continue...")

            elif choice == "3":
                contributor = input("Filter by contributor (leave blank for overall ranking): ").strip() or None
                language = input("Filter by language (optional): ").strip() or None
                skill = input("Filter by skill (optional): ").strip() or None
                since_str = input("Only include analyses since (YYYY-MM-DD, optional): ").strip() or None
                since_dt = parse_date(since_str)
                top_n_raw = input("How many projects to show? [default 5]: ").strip()
                try:
                    top_n = int(top_n_raw) if top_n_raw else 5
                except ValueError:
                    print("[INFO] Invalid number; defaulting to 5.")
                    top_n = 5

                ranked = list_project_insights(storage_path=storage_path)
                ranked = filter_insights(
                    ranked,
                    language=language,
                    skill=skill,
                    since=since_dt,
                )
                if contributor:
                    ranked = rank_projects_by_contribution(
                        storage_path=storage_path,
                        contributor=contributor,
                        top_n=None,
                    )
                    ranked = filter_insights(ranked, language=language, skill=skill, since=since_dt)

                ranked = sorted(
                    ranked,
                    key=lambda ins: compute_composite_score(ins, contributor=contributor)[0],
                    reverse=True,
                )
                if top_n >= 0:
                    ranked = ranked[:top_n]

                if not ranked:
                    print("[INFO] No insights recorded yet.")
                else:
                    print("\nProject ranking:\n")
                    for i, item in enumerate(ranked, start=1):
                        score, parts = compute_composite_score(item, contributor=contributor)
                        reason = (
                            f"base={parts['base']}, "
                            f"recency={parts['recency']:.2f}, "
                            f"skills={parts['skills']:.2f}"
                        )
                        print(
                            f"{i}) {item.project_name} | composite={score:.2f} | "
                            f"contributors={item.stats.get('contributors')} | {reason}"
                        )
                input("\nPress Enter to continue...")

            elif choice == "4":
                contributor = input("Filter by contributor (leave blank for overall ranking): ").strip() or None
                language = input("Filter by language (optional): ").strip() or None
                skill = input("Filter by skill (optional): ").strip() or None
                since_str = input("Only include analyses since (YYYY-MM-DD, optional): ").strip() or None
                since_dt = parse_date(since_str)
                top_n_raw = input("How many top projects to summarize? [default 3]: ").strip()
                try:
                    top_n = int(top_n_raw) if top_n_raw else 3
                except ValueError:
                    print("[INFO] Invalid number; defaulting to 3.")
                    top_n = 3

                insights = list_project_insights(storage_path=storage_path)
                insights = filter_insights(
                    insights,
                    language=language,
                    skill=skill,
                    since=since_dt,
                )
                if contributor:
                    insights = rank_projects_by_contribution(
                        storage_path=storage_path,
                        contributor=contributor,
                        top_n=None,
                    )
                    insights = filter_insights(insights, language=language, skill=skill, since=since_dt)

                summaries = sorted(
                    insights,
                    key=lambda ins: compute_composite_score(ins, contributor=contributor)[0],
                    reverse=True,
                )
                summaries = summaries[:top_n] if top_n >= 0 else []

                if not summaries:
                    print("[INFO] No insights recorded yet.")
                else:
                    print("\nTop-ranked project summaries:\n")
                    for i, insight in enumerate(summaries, start=1):
                        score, parts = compute_composite_score(insight, contributor=contributor)
                        rationale = (
                            f"base={parts['base']}, recency={parts['recency']:.2f}, "
                            f"skills={parts['skills']:.2f}"
                        )
                        print(
                            f"{i}) {insight.project_name} | composite={score:.2f}"
                        )
                        print(f"    summary: {insight.summary or '—'}")
                        print(f"    rationale: {rationale}")
                input("\nPress Enter to continue...")

            elif choice == "0":
                return

            else:
                print("Please choose a valid option (0-4).")

        except Exception as e:
            print(f"[ERROR] {e}")
            input("Press Enter to return to insights menu...")
            return
