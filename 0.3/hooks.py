"""Module declaring the hooks for Mkdocs."""

import json
import os
from dataclasses import dataclass
from typing import Dict, List

from mkdocs.config.defaults import MkDocsConfig
from mkdocs.structure.nav import Page


@dataclass
class DynamicEntry:
    """Represents a dynamic entry for a data table : the data will be pulled
    from the results files.
    """

    name: str
    results: Dict
    additional_fields: List[str]


def on_page_markdown(markdown: str, page: Page, config: MkDocsConfig, **kwargs) -> str:
    """Function that runs before rendering the markdown.

    See https://www.mkdocs.org/dev-guide/plugins/#events for more details.

    Args:
        markdown (str): The markdown content of the page.
        page (Page): The page being rendered.
        config (MkDocsConfig): The configuration.
        **kwargs: Keywords arguments to pass to the given function.

    Returns:
        str: The updated markdown content.
    """
    if "leaderboards" in page.file.src_uri:
        lines = markdown.split("\n")
        entries = []
        for line in lines:
            if line.startswith(">>>"):
                # This is a line with a path to a result file
                # -> parse it and extract the results
                name, result_file_path, *args = line[3:].split("|")

                with open(os.path.join(config.docs_dir, result_file_path), "r") as f:
                    res = json.load(f)

                entries.append(DynamicEntry(name, res, args))

        # Each leaderboard implements its own render logic
        rendered_entries = [None for _ in entries]
        if page.file.src_uri.endswith("main.md"):
            rendered_entries = render_main(entries)
        elif page.file.src_uri.endswith("compare.md"):
            rendered_entries = render_compare(entries)

        # Replace the lines accordingly
        for i, line in enumerate(lines):
            if line.startswith(">>>"):
                lines[i] = rendered_entries.pop(0)

        return "\n".join(lines)


def render_main(entries: List[DynamicEntry]) -> List[str]:
    """Code for rendering the leaderboard : `leaderboards/main.md`."""
    # Extract the scores we are going to use
    for e in entries:
        e.score = e.results["overall_score"]
        e.nwp = e.results["next_word_prediction"]["score"]["top3_accuracy"]
        e.acp = e.results["auto_completion"]["score"]["top3_accuracy"]
        e.acr = e.results["auto_correction"]["score"]["fscore"]

    # Sort entries according to the overall score
    entries.sort(reverse=True, key=lambda e: e.score)

    # Find the best scores to highlight for each column
    best_score = max(e.score for e in entries)
    best_nwp = max(e.nwp for e in entries)
    best_acp = max(e.acp for e in entries)
    best_acr = max(e.acr for e in entries)

    # Render the entries
    rendered_entries = []
    for e in entries:
        score = f"{round(e.score, 2):g}"
        nwp = f"{round(e.nwp, 2):g}"
        acp = f"{round(e.acp, 2):g}"
        acr = f"{round(e.acr, 2):g}"

        # Highlight the best scores
        if e.score == best_score:
            score = f"**{score}**"
        if e.nwp == best_nwp:
            nwp = f"**{nwp}**"
        if e.acp == best_acp:
            acp = f"**{acp}**"
        if e.acr == best_acr:
            acr = f"**{acr}**"

        # Render
        rendered_entries.append(f"| {e.name} | {score} | {acr} | {acp} | {nwp} |")

    return rendered_entries


def render_compare(entries: List[DynamicEntry]) -> List[str]:
    """Code for rendering the leaderboard : `leaderboards/compare.md`."""
    # Extract the scores we are going to use
    for e in entries:
        e.score = e.results["overall_score"]
        e.nwp = e.results["next_word_prediction"]["score"]["top3_accuracy"]
        e.acp = e.results["auto_completion"]["score"]["top3_accuracy"]
        e.acr_detection = e.results["auto_correction"]["score"]["recall"]
        e.acr_frustration = 1 - e.results["auto_correction"]["score"]["precision"]

    # Sort entries according to the overall score
    entries.sort(reverse=True, key=lambda e: e.score)

    # Find the best scores to highlight for each column
    best_score = max(e.score for e in entries)
    best_nwp = max(e.nwp for e in entries)
    best_acp = max(e.acp for e in entries)
    best_acr_detection = max(e.acr_detection for e in entries)
    best_acr_frustration = min(e.acr_frustration for e in entries)

    # Render the entries
    rendered_entries = []
    for e in entries:
        score = f"{round(e.score * 1000)}"
        nwp = f"{round(e.nwp * 100)}%"
        acp = f"{round(e.acp * 100)}%"
        acr_detection = f"{round(e.acr_detection * 100)}%"
        acr_frustration = f"{round(e.acr_frustration * 100)}%"

        # Highlight the best scores
        if e.score == best_score:
            score = f"**{score}**"
        if e.nwp == best_nwp:
            nwp = f"**{nwp}**"
        if e.acp == best_acp:
            acp = f"**{acp}**"
        if e.acr_detection == best_acr_detection:
            acr_detection = f"**{acr_detection}**"
        if e.acr_frustration == best_acr_frustration:
            acr_frustration = f"**{acr_frustration}**"

        # Render
        additional_fields = " | ".join(e.additional_fields)
        if additional_fields != "":
            rendered_entries.append(
                f"| {e.name} | {score} | {acr_detection} | {acr_frustration} | {acp} | {nwp} | {additional_fields} |"
            )
        else:
            rendered_entries.append(f"| {e.name} | {score} | {acr_detection} | {acr_frustration} | {acp} | {nwp} |")

    return rendered_entries
