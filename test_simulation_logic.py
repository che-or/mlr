import pandas as pd
from itertools import product
import sys
import os

# Ensure the 'scripts' directory is in the Python path
sys.path.append(os.path.join(os.path.dirname(__file__)))

from scripts.simulate_play import _simulate_play

# --- CONFIGURATION ---

PITCHERS = {'1B': '1', '2B': '2', '3B': '3', 'Batter': 'H'}
INITIAL_OUTS = [0, 1, 2]
ORDERED_BASE_CONFIGS = [
    (False, False, False), (True, False, False), (False, True, False), (False, False, True),
    (True, True, False), (True, False, True), (False, True, True), (True, True, True)
]

# --- SVG AND FORMATTING HELPERS ---

def generate_diamond_svg(runners, runs_scored=[], size=70): # Increased size
    """Generates a theme-aware SVG for the base diamond graphic with final adjustments."""
    canvas_size = size
    draw_area_size = 60 # Increased drawing area
    offset = (canvas_size - draw_area_size) / 2

    s = draw_area_size
    w = s * 0.3 # Increased base width
    p = s * 0.05
    
    second_x = (s/2 - w/2) + offset
    second_y = p + offset
    third_x = p + offset
    third_y = (s/2 - w/2) + offset
    first_x = (s - w - p) + offset
    first_y = (s/2 - w/2) + offset
    home_x = (s/2 - w/2) + offset
    home_y = (s - w - p) + offset

    centers = {
        '1B': (first_x + w/2, first_y + w/2), '2B': (second_x + w/2, second_y + w/2),
        '3B': (third_x + w/2, third_y + w/2), 'H': (home_x + w/2, home_y + w/2)
    }

    runner_1b, runner_2b, runner_3b = runners
    fills = {
        '1B': "white" if runner_1b else "none", # Use 'none' for empty fill
        '2B': "white" if runner_2b else "none",
        '3B': "white" if runner_3b else "none"
    }

    svg = f'<svg width="{canvas_size}" height="{canvas_size}" viewBox="0 0 {canvas_size} {canvas_size}" xmlns="http://www.w3.org/2000/svg" style="vertical-align: middle;">'
    
    svg += f'<rect x="{second_x}" y="{second_y}" width="{w}" height="{w}" fill="{fills["2B"]}" stroke="white" stroke-width="2" transform="rotate(45 {centers["2B"][0]} {centers["2B"][1]})"/>'
    svg += f'<rect x="{third_x}" y="{third_y}" width="{w}" height="{w}" fill="{fills["3B"]}" stroke="white" stroke-width="2" transform="rotate(45 {centers["3B"][0]} {centers["3B"][1]})"/>'
    svg += f'<rect x="{first_x}" y="{first_y}" width="{w}" height="{w}" fill="{fills["1B"]}" stroke="white" stroke-width="2" transform="rotate(45 {centers["1B"][0]} {centers["1B"][1]})"/>'

    if runs_scored:
        # Gold outline for runs plate
        svg += f'<rect x="{home_x}" y="{home_y}" width="{w}" height="{w}" fill="gold" stroke="gold" stroke-width="2" transform="rotate(45 {centers["H"][0]} {centers["H"][1]})"/>'

    base_text_style = f'font-family: monospace, sans-serif; text-anchor: middle; dominant-baseline: central; font-weight: bold;'
    
    # Increased font size
    font_size = w * 0.8
    if runner_1b: svg += f'<text x="{centers["1B"][0]}" y="{centers["1B"][1]}" fill="black" style="{base_text_style} font-size:{font_size}px;">{runner_1b}</text>'
    if runner_2b: svg += f'<text x="{centers["2B"][0]}" y="{centers["2B"][1]}" fill="black" style="{base_text_style} font-size:{font_size}px;">{runner_2b}</text>'
    if runner_3b: svg += f'<text x="{centers["3B"][0]}" y="{centers["3B"][1]}" fill="black" style="{base_text_style} font-size:{font_size}px;">{runner_3b}</text>'

    if runs_scored:
        sort_order = {'3': 0, '2': 1, '1': 2, 'H': 3}
        sorted_runners = sorted(runs_scored, key=lambda r: sort_order.get(r, 99))
        label_text = "".join(sorted_runners)
        
        svg_text_block = f'<text x="{centers["H"][0]}" y="{centers["H"][1]}" fill="black" style="{base_text_style}">'
        if len(label_text) > 2:
            line1 = label_text[:2]
            line2 = label_text[2:]
            font_size = w * 0.5
            line_height = font_size
            svg_text_block += f'<tspan x="{centers["H"][0]}" dy="-{line_height/2}px" style="font-size:{font_size}px;">{line1}</tspan>'
            svg_text_block += f'<tspan x="{centers["H"][0]}" dy="{line_height}px" style="font-size:{font_size}px;">{line2}</tspan>'
        else:
            font_size = w * 0.7
            svg_text_block += f'<tspan style="font-size:{font_size}px;">{label_text}</tspan>'
        svg_text_block += '</text>'
        svg += svg_text_block

    svg += '</svg>'
    return svg

def generate_outs_svg(initial_outs, outs_on_play, height=16, r=7):
    """Generates a theme-aware SVG for the three-circle outs display with spacing."""
    fills = ["none"] * 3 # Use 'none' for empty fill
    for i in range(3):
        if i < initial_outs: fills[i] = "white"
        elif i < initial_outs + outs_on_play: fills[i] = "gold"

    spacing = 4
    circle_diameter = r * 2
    content_width = (circle_diameter * 3) + (spacing * 2)
    svg_width = content_width + 2
    
    cx1 = r + 1
    cx2 = cx1 + circle_diameter + spacing
    cx3 = cx2 + circle_diameter + spacing

    svg = f'<svg width="{svg_width}" height="{height}" viewBox="-1 -1 {svg_width+2} {height+2}" xmlns="http://www.w3.org/2000/svg" style="vertical-align: middle;">'
    svg += f'<circle cx="{cx1}" cy="{height/2}" r="{r}" fill="{fills[0]}" stroke="white" stroke-width="2"/>'
    svg += f'<circle cx="{cx2}" cy="{height/2}" r="{r}" fill="{fills[1]}" stroke="white" stroke-width="2"/>'
    svg += f'<circle cx="{cx3}" cy="{height/2}" r="{r}" fill="{fills[2]}" stroke="white" stroke-width="2"/>'
    svg += '</svg>'
    return svg

def config_to_runners(config):
    runners = [None, None, None]
    if config[0]: runners[0] = PITCHERS['1B']
    if config[1]: runners[1] = PITCHERS['2B']
    if config[2]: runners[2] = PITCHERS['3B']
    return runners

def determine_old_result(result, outs_on_play, runs_scored, initial_outs, config, test_conditions):
    old_result = result
    if result.startswith('STEAL') or result.startswith('MSTEAL'): return 'SB'
    if result.startswith('CS') or result.startswith('CMS'): return 'CS'
    if result == 'FO' and config[2] and initial_outs < 2 and PITCHERS['3B'] in runs_scored: return 'Sac'
    if outs_on_play == 3: return 'TP'
    if outs_on_play == 2 and result != 'BUNT DP':
        is_high_diff = test_conditions.get('diff', 0) >= 496
        is_modern_season = test_conditions.get('season', 0) >= 9
        if result == 'LGO' and is_high_diff and is_modern_season: return 'LO'
        else: return 'DP'
    return old_result

def run_test_matrix(result, test_conditions):
    columns = [generate_diamond_svg(config_to_runners(c), []) for c in ORDERED_BASE_CONFIGS]
    df = pd.DataFrame(index=INITIAL_OUTS, columns=columns)
    df.index.name = "Initial Outs"

    for outs in INITIAL_OUTS:
        for config in ORDERED_BASE_CONFIGS:
            initial_runners = config_to_runners(config)
            
            final_runners, outs_on_play, runs_scored = _simulate_play(
                runners_before_play=initial_runners, current_outs=outs, result=result,
                current_pitcher_id=PITCHERS['Batter'], **test_conditions
            )

            if final_runners == 'Invalid Result':
                cell_content = "**Invalid Result**"
            else:
                old_result_str = f"**{determine_old_result(result, outs_on_play, runs_scored, outs, config, test_conditions)}**"
                final_state_svg = generate_diamond_svg(final_runners, runs_scored)
                outs_svg = generate_outs_svg(outs, outs_on_play)
                
                cell_parts = [old_result_str, final_state_svg, outs_svg]
                cell_content = "<br>".join(cell_parts)
            
            df.loc[outs, generate_diamond_svg(initial_runners, [])] = cell_content
            
    return df

def main():
    scenarios_to_run = [
        {"name": "RESULT: HR", "result": 'HR', "conditions": {'season': 12, 'diff': 0, 'pa_type': 1}},
        {"name": "RESULT: 3B", "result": '3B', "conditions": {'season': 12, 'diff': 0, 'pa_type': 1}},
        {"name": "RESULT: 2B", "result": '2B', "conditions": {'season': 12, 'diff': 0, 'pa_type': 1}},
        {"name": "RESULT: 1B", "result": '1B', "conditions": {'season': 12, 'diff': 0, 'pa_type': 1}},
        {"name": "RESULT: BB", "result": 'BB', "conditions": {'season': 12, 'diff': 0, 'pa_type': 1}},
        {"name": "RESULT: IBB", "result": 'IBB', "conditions": {'season': 12, 'diff': 0, 'pa_type': 1}},
        {"name": "RESULT: AUTO BB", "result": 'AUTO BB', "conditions": {'season': 12, 'diff': 0, 'pa_type': 1}},
        {"name": "RESULT: FO", "result": 'FO', "conditions": {'season': 12, 'diff': 0, 'pa_type': 1}},
        {"name": "RESULT: K", "result": 'K', "conditions": {'season': 12, 'diff': 0, 'pa_type': 1}},
        {"name": "RESULT: AUTO K", "result": 'AUTO K', "conditions": {'season': 12, 'diff': 0, 'pa_type': 1}},
        {"name": "RESULT: PO", "result": 'PO', "conditions": {'season': 12, 'diff': 0, 'pa_type': 1}},
        {"name": "RESULT: RGO", "result": 'RGO', "conditions": {'season': 12, 'diff': 0, 'pa_type': 1}},
        {"name": "RESULT: RGO (Infield In)", "result": 'RGO', "conditions": {'season': 12, 'diff': 0, 'pa_type': 2}},
        {"name": "RESULT: LGO", "result": 'LGO', "conditions": {'season': 12, 'diff': 0, 'pa_type': 1}},
        {"name": "RESULT: LGO (Infield In)", "result": 'LGO', "conditions": {'season': 12, 'diff': 0, 'pa_type': 2}},
        {"name": "RESULT: LGO (High Diff, Modern Season >= 9)", "result": 'LGO', "conditions": {'season': 10, 'diff': 500, 'pa_type': 1}},
        {"name": "RESULT: LGO (High Diff, Old Season < 9)", "result": 'LGO', "conditions": {'season': 8, 'diff': 500, 'pa_type': 1}},
        {"name": "RESULT: BUNT 1B", "result": 'BUNT 1B', "conditions": {'season': 12, 'diff': 0, 'pa_type': 1}},
        {"name": "RESULT: BUNT SAC", "result": 'BUNT SAC', "conditions": {'season': 12, 'diff': 0, 'pa_type': 1}},
        {"name": "RESULT: BUNT K", "result": 'BUNT K', "conditions": {'season': 12, 'diff': 0, 'pa_type': 1}},
        {"name": "RESULT: BUNT GO", "result": 'BUNT GO', "conditions": {'season': 12, 'diff': 0, 'pa_type': 1}},
        {"name": "RESULT: BUNT DP", "result": 'BUNT DP', "conditions": {'season': 12, 'diff': 0, 'pa_type': 1}},
        {"name": "RESULT: STEAL 2B", "result": 'STEAL 2B', "conditions": {'season': 12, 'diff': 0, 'pa_type': 1}},
        {"name": "RESULT: STEAL 3B", "result": 'STEAL 3B', "conditions": {'season': 12, 'diff': 0, 'pa_type': 1}},
        {"name": "RESULT: STEAL HOME", "result": 'STEAL HOME', "conditions": {'season': 12, 'diff': 0, 'pa_type': 1}},
        {"name": "RESULT: CS 2B", "result": 'CS 2B', "conditions": {'season': 12, 'diff': 0, 'pa_type': 1}},
        {"name": "RESULT: CS 3B", "result": 'CS 3B', "conditions": {'season': 12, 'diff': 0, 'pa_type': 1}},
        {"name": "RESULT: CS HOME", "result": 'CS HOME', "conditions": {'season': 12, 'diff': 0, 'pa_type': 1}},
        {"name": "RESULT: MSTEAL 3B", "result": 'MSTEAL 3B', "conditions": {'season': 12, 'diff': 0, 'pa_type': 1}},
        {"name": "RESULT: MSTEAL HOME", "result": 'MSTEAL HOME', "conditions": {'season': 12, 'diff': 0, 'pa_type': 1}},
        {"name": "RESULT: CMS 3B", "result": 'CMS 3B', "conditions": {'season': 12, 'diff': 0, 'pa_type': 1}},
        {"name": "RESULT: CMS HOME", "result": 'CMS HOME', "conditions": {'season': 12, 'diff': 0, 'pa_type': 1}},
    ]

    output_filename = "simulation_test_results.md"

    with open(output_filename, "w", encoding="utf-8") as f:
        f.write("# Simulation Logic Test Results\n\n")
        for scenario in scenarios_to_run:
            f.write(f"### {scenario['name']}\n\n")
            df = run_test_matrix(scenario['result'], scenario['conditions'])
            f.write(df.to_markdown(colalign=["center"] * (len(df.columns) + 1)))
            f.write("\n\n")
    
    print(f"Successfully generated final graphical test results in '{output_filename}'")

if __name__ == "__main__":
    main()