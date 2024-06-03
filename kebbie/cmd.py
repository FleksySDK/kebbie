"""Module containing the implementation for the `kebbie` command line."""

import argparse
import json
import sys
import xml.etree.ElementTree as ET
from typing import List

from kebbie import emulator, evaluate
from kebbie.correctors import EmulatorCorrector
from kebbie.emulator import Emulator
from kebbie.utils import get_soda_dataset


def instantiate_correctors(
    keyboard: str, get_layout: bool = True, fast_mode: bool = True, instantiate_emulator: bool = True
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
        get_layout (bool, optional):  If `True`, The keyboard keys and suggestions
            will be mapped and shown on screen.

    Returns:
        The list of created Correctors.
    """
    if keyboard in ["gboard", "tappa", "swiftkey", "yandex"]:
        # Android keyboards
        return [
            EmulatorCorrector(
                device=d,
                platform="android",
                keyboard=keyboard,
                fast_mode=fast_mode,
                instantiate_emulator=instantiate_emulator,
                get_layout=get_layout,
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
                get_layout=get_layout,
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
        choices=["gboard", "ios", "kbkitpro", "kbkitoss", "tappa", "fleksy", "swiftkey", "yandex"],
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

    page_source_parser = subparsers.add_parser(
        "get_page_source", help="Save the page source of the keyboard in a file for debugging purpose."
    )
    page_source_parser.set_defaults(cmd="get_page_source")
    common_args(page_source_parser)
    page_source_parser.add_argument(
        "--page_source_file",
        "-F",
        dest="page_source_file",
        type=str,
        default="keyboard_page_source.xml",
        help="Where to save the keyboard page source",
    )
    page_source_parser.add_argument(
        "--print_page_source",
        "-P",
        dest="print_page_source",
        action="store_true",
        default=False,
        help="If specified, the page source will be shown in console too.",
    )

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

    elif args.cmd == "get_page_source":
        correctors = instantiate_correctors(args.keyboard, get_layout=False)

        for c in correctors:
            # Get the page source
            page_source = ET.fromstring(c.emulator.driver.page_source)

            # Get the keyboard package name
            keyboard_package = emulator.KEYBOARD_PACKAGE.get(args.keyboard, None)

            if keyboard_package:
                # Filter elements that have the specified package
                filtered_elements = [element for element in page_source if element.get("package") == keyboard_package]

                if filtered_elements:
                    # If there are filtered elements, create a new XML with those elements
                    filtered_page_source = ET.Element(page_source.tag, page_source.attrib)
                    filtered_page_source.extend(filtered_elements)
                    page_source = filtered_page_source

            page_source_str = ET.tostring(page_source, encoding="utf8").decode("utf8")

            # Print the keyboard elements to the console if specified
            if args.print_page_source:
                print(page_source_str)

            # Save the keyboard elements to a file
            with open(args.page_source_file, "w", encoding="utf-8") as file:
                file.write(page_source_str)
