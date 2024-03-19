"""Module containing the implementation for the `kebbie` command line."""
import argparse
import sys

from kebbie.emulator import Emulator


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

    layout_parser = subparsers.add_parser(
        "show_layout", help="Display the layout over the keyboard for debugging purpose."
    )
    layout_parser.set_defaults(cmd="show_layout")

    args = parser.parse_args()

    if args.cmd is None:
        parser.print_help(sys.stderr)
        sys.exit(1)
    elif args.cmd == "evaluate":
        raise NotImplementedError()
    elif args.cmd == "show_layout":
        e = Emulator("android", "gboard")
        e.show_keyboards()
        print("Predictions : ", e.get_predictions())
