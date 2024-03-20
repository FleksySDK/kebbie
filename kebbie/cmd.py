"""Module containing the implementation for the `kebbie` command line."""
import argparse
import json
import sys

from kebbie import evaluate
from kebbie.correctors import EmulatorCorrector
from kebbie.emulator import Emulator
from kebbie.utils import get_soda_dataset


def cli():
    """Entry-point of the `kebbie` command line.

    Raises:
        NotImplementedError: Temporary.
    """
    # create the top-level parser
    parser = argparse.ArgumentParser(description="Kebbie's command line.")
    subparsers = parser.add_subparsers(title="commands", dest="cmd")

    evaluate_parser = subparsers.add_parser("evaluate", help="Run the evaluation using emulated keyboard.")
    evaluate_parser.set_defaults(cmd="evaluate")
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
        default=250,
        help="The number of sentences to use for the evaluation. Emulated keyboard are slow, so we can't run on the "
        "full test set. Instead we pick the first N sentences.",
    )

    layout_parser = subparsers.add_parser(
        "show_layout", help="Display the layout over the keyboard for debugging purpose."
    )
    layout_parser.set_defaults(cmd="show_layout")

    args = parser.parse_args()

    if args.cmd is None:
        parser.print_help(sys.stderr)
        sys.exit(1)
    elif args.cmd == "evaluate":
        # Create one corrector per device
        # TODO : get the right keyboard
        correctors = [
            EmulatorCorrector(
                device=d,
                platform="android",
                keyboard="gboard",
                fast_mode=not args.all_tasks,
                instantiate_emulator=False,
            )
            for d in Emulator.get_devices()
        ]

        # Get dataset, and filter it to keep only a small number of sentences
        dataset = get_soda_dataset(args.n_sentences)

        # Run the evaluation
        results = evaluate(correctors, dataset=dataset)

        # Save the results in a file
        with open(args.result_file, "w", encoding="utf-8") as f:
            json.dump(results, f, ensure_ascii=False, indent=4)

    elif args.cmd == "show_layout":
        # TODO : get the right keyboard
        e = Emulator("android", "gboard")
        e.show_keyboards()
        print("Predictions : ", e.get_predictions())
