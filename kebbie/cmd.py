"""Module containing the implementation for the `kebbie` command line."""

import argparse
import json
import sys
from typing import List

from kebbie import evaluate
from kebbie.correctors import EmulatorCorrector
from kebbie.emulator import Emulator
from kebbie.utils import get_soda_dataset


def instantiate_correctors(
    keyboard: str, fast_mode: bool = True, instantiate_emulator: bool = True
) -> List[EmulatorCorrector]:
    """Create the right correctors (with the right platform, etc...) given the
    arguments from the command line.

    Args:
        keyboard (str): Name fo the keyboard to load.
        fast_mode (bool, optional): If `True`, the corrector will be
            instantiated in fast mode (only AC).
        instantiate_emulator (bool, optional): If `True`, the emulators are
            instantiated (which trigger the layout detection). If `False`, only
            the corrector is instantiated, not the emulator.

    Returns:
        The list of created Correctors.
    """
    if keyboard in ["gboard", "tappa"]:
        # Android keyboards
        return [
            EmulatorCorrector(
                device=d,
                platform="android",
                keyboard=keyboard,
                fast_mode=fast_mode,
                instantiate_emulator=instantiate_emulator,
            )
            for d in Emulator.get_android_devices()
        ]
    else:
        # iOS keyboards
        return [
            EmulatorCorrector(
                device=i,
                platform="ios",
                keyboard=keyboard,
                fast_mode=fast_mode,
                instantiate_emulator=instantiate_emulator,
                ios_name=ios_name,
                ios_platform=ios_platform,
            )
            for i, (ios_platform, ios_name) in enumerate(Emulator.get_ios_devices())
        ]


def common_args(parser: argparse.ArgumentParser):
    """Add common arguments to the given parser.

    Args:
        parser (argparse.ArgumentParser): Parser where to add the arguments.
    """
    parser.add_argument(
        "--keyboard",
        "-K",
        dest="keyboard",
        type=str,
        required=True,
        choices=["gboard", "ios", "tappa"],
        help="Which keyboard, to be tested, is currently installed on the emulator.",
    )


def cli():
    """Entry-point of the `kebbie` command line."""
    # create the top-level parser
    parser = argparse.ArgumentParser(description="Kebbie's command line.")
    subparsers = parser.add_subparsers(title="commands", dest="cmd")

    evaluate_parser = subparsers.add_parser("evaluate", help="Run the evaluation using emulated keyboard.")
    evaluate_parser.set_defaults(cmd="evaluate")
    common_args(evaluate_parser)
    evaluate_parser.add_argument(
        "--result_file",
        "-R",
        dest="result_file",
        type=str,
        default="results.json",
        help="When to save the results of the evaluation",
    )
    evaluate_parser.add_argument(
        "--all_tasks",
        "-A",
        dest="all_tasks",
        action="store_true",
        default=False,
        help="If specified, all tasks are evaluated (not only auto-correction, but also auto-completion and "
        "next-word prediction).",
    )
    evaluate_parser.add_argument(
        "--n_sentences",
        "-N",
        dest="n_sentences",
        type=int,
        default=100,
        help="The number of sentences to use for the evaluation. Emulated keyboard are slow, so we can't run on the "
        "full test set. Instead we pick the first N sentences.",
    )
    evaluate_parser.add_argument(
        "--track_mistakes",
        "-T",
        dest="track_mistakes",
        action="store_true",
        default=False,
        help="If specified, mistakes will be tracked and saved in the result file.",
    )

    layout_parser = subparsers.add_parser(
        "show_layout", help="Display the layout over the keyboard for debugging purpose."
    )
    layout_parser.set_defaults(cmd="show_layout")
    common_args(layout_parser)

    args = parser.parse_args()

    if args.cmd is None:
        parser.print_help(sys.stderr)
        sys.exit(1)
    elif args.cmd == "evaluate":
        correctors = instantiate_correctors(args.keyboard, fast_mode=not args.all_tasks, instantiate_emulator=False)

        # Get dataset, and filter it to keep only a small number of sentences
        dataset = get_soda_dataset(args.n_sentences)

        # Run the evaluation
        results = evaluate(correctors, dataset=dataset, track_mistakes=args.track_mistakes)

        # Save the results in a file
        with open(args.result_file, "w", encoding="utf-8") as f:
            json.dump(results, f, ensure_ascii=False, indent=4)

        print("Overall score : ", results["overall_score"])

    elif args.cmd == "show_layout":
        correctors = instantiate_correctors(args.keyboard)
        for c in correctors:
            c.emulator.show_keyboards()
            print(f"Predictions : {c.emulator.get_predictions()}")
