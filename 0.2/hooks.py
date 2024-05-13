"""Module declaring the hooks for Mkdocs."""

import json
import os

from mkdocs.config.defaults import MkDocsConfig
from mkdocs.structure.nav import Page


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
    if page.file.src_uri == "leaderboard.md":
        lines = markdown.split("\n")
        entries = []
        for line in lines:
            if line.startswith(">>>"):
                # This is a line with a path to a result file
                # -> parse it and extract the results
                kb_name, result_file_path = line[3:].split("|")

                with open(os.path.join(config.docs_dir, result_file_path), "r") as f:
                    res = json.load(f)

                entries.append(
                    {
                        "kb_name": kb_name,
                        "score": res["overall_score"],
                        "nwp": res["next_word_prediction"]["score"]["top3_accuracy"],
                        "acp": res["auto_completion"]["score"]["top3_accuracy"],
                        "acr": res["auto_correction"]["score"]["fscore"],
                    }
                )

        # Sort according to the overall score
        entries.sort(reverse=True, key=lambda x: x["score"])

        # Find the best scores to highlight
        best_score = max(entries, key=lambda x: x["score"])["score"]
        best_nwp = max(entries, key=lambda x: x["nwp"])["nwp"]
        best_acp = max(entries, key=lambda x: x["acp"])["acp"]
        best_acr = max(entries, key=lambda x: x["acr"])["acr"]

        # Replace the lines accordingly
        for i, line in enumerate(lines):
            if line.startswith(">>>"):
                e = entries.pop(0)

                score = f"{round(e['score'], 2):g}"
                nwp = f"{round(e['nwp'], 2):g}"
                acp = f"{round(e['acp'], 2):g}"
                acr = f"{round(e['acr'], 2):g}"

                # Highlight the best scores
                if e["score"] == best_score:
                    score = f"**{score}**"
                if e["nwp"] == best_nwp:
                    nwp = f"**{nwp}**"
                if e["acp"] == best_acp:
                    acp = f"**{acp}**"
                if e["acr"] == best_acr:
                    acr = f"**{acr}**"

                # Overwrite the line
                lines[i] = f"| {e['kb_name']} | {score} | {nwp} | {acp} | {acr} |"

        return "\n".join(lines)
