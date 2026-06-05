import pandas as pd
import json
from pathlib import Path


def _get_base_state_svg(obc):
    bases = {"first": bool(obc & 1), "second": bool(obc & 2), "third": bool(obc & 4)}
    def diamond(filled, points):
        color = "#D7DADC" if filled else "none"
        return f'<polygon points="{points}" fill="{color}" stroke="#D7DADC" stroke-width="1.5"/>'
    return "".join([
        '<svg width="24" height="24" viewbox="0 0 24 24">',
        diamond(bases["second"], "12,2 17,7 12,12 7,7"),
        diamond(bases["third"], "5,9 10,14 5,19 0,14"),
        diamond(bases["first"], "19,9 24,14 19,19 14,14"),
        "</svg>",
    ])


def _generate_re_matrix_html(season_num):
    csv_path = Path(__file__).parent / ".." / "data" / "re_matrices" / f"mlr_re_matrix_S{season_num}.csv"
    if not csv_path.exists():
        return None
    re_df = pd.read_csv(csv_path)
    matrix = {(int(r["OBC"]), int(r["Outs"])): float(r["RE"]) for _, r in re_df.iterrows()}
    html = "<table class='stats-table re-matrix'><thead><tr><th>Outs</th>"
    for obc in range(8):
        html += f"<th>{_get_base_state_svg(obc)}</th>"
    html += "</tr></thead><tbody>"
    for outs in range(3):
        html += f"<tr><td><strong>{outs}</strong></td>"
        for obc in range(8):
            html += f"<td>{matrix.get((obc, outs), 0.0):.3f}</td>"
        html += "</tr>"
    html += "</tbody></table>"
    return {"title": f"Run Expectancy Matrix (S{season_num})", "blocks": [{"type": "html", "value": html}]}


def update_glossary_re_matrix(season_num):
    glossary_path = Path(__file__).parent / ".." / "docs" / "glossary.json"
    try:
        with open(glossary_path, "r") as f:
            glossary_data = json.load(f)
        section = _generate_re_matrix_html(season_num)
        if section and "RE24" in glossary_data:
            glossary_data["RE24"]["sections"] = [
                s for s in glossary_data["RE24"]["sections"]
                if "Run Expectancy Matrix" not in s["title"]
            ]
            glossary_data["RE24"]["sections"].append(section)
            with open(glossary_path, "w") as f:
                json.dump(glossary_data, f, indent=2)
            print(f"Glossary updated with RE Matrix for S{season_num}.")
    except (FileNotFoundError, json.JSONDecodeError, KeyError) as e:
        print(f"Warning: Could not update glossary.json. Error: {e}")
