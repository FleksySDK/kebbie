"""Module containing the helpers `LayoutHelper`, useful class to deal with the
layout of a keyboard, access key positions, etc...
"""

from collections import defaultdict
from dataclasses import dataclass
from typing import Dict, List, Optional, Tuple

import regex as re

from kebbie.utils import euclidian_dist, load_keyboard


SPACE = "spacebar"
POINT = "."
N_ACCENT_PER_LINE = 4


@dataclass
class KeyInfo:
    """Structure containing all information needed for a given character (key).

    Args:
        klayer_id (int): Keyboard Layer ID where this key is located.
        width (float): Width of the key.
        height (float): Height of the key.
        center (Tuple[float, float]): Center position (x, y coordinates) of the
            key.
    """

    klayer_id: int
    width: float
    height: float
    center: Tuple[float, float]


@dataclass
class Key:
    """Structure containing information needed for each key of a given keyboard
    layer.

    Args:
        char (str): Character associated with this key.
        bounds (Dict[str, float]): Dictionary representing the bounding box of
            the key. The dictionary should contains the following keys :
            `right`, `left`, `top`, `bottom`.
    """

    char: str
    bounds: Dict[str, float]


class LayoutHelper:
    """Small class that represents a Keyboard layout. The goal of this class is
    to offer some easy-to-use method to deal with a keyboard layout.

    Args:
        lang (str, optional): Language of the layout to load.
        custom_keyboard (Dict, optional): If provided, instead of relying on
            the keyboard layout provided by default, uses the given keyboard
            layout.
        ignore_layers_after (Optional[int]) : Ignore higher layers of the
            keyboard layout. If `None` is given, no layer is ignored.
    """

    def __init__(self, lang: str = "en-US", custom_keyboard: Dict = None, ignore_layers_after: Optional[int] = None):
        keyboard = custom_keyboard if custom_keyboard is not None else load_keyboard(lang)
        self.keys_info, self.klayers_info, self.accents = self._extract_infos(keyboard["layout"], ignore_layers_after)
        self.letter_accents = [c for c in self.accents if re.match(r"^[\pL]+$", c)]
        self.spelling_symbols = keyboard["settings"]["allowed_symbols_in_words"]
        self.layout_name = keyboard["keyboard"]["default-layout"]

    def _extract_infos(  # noqa: C901
        self, keyboard_layout: Dict, ignore_layers_after: Optional[int] = None
    ) -> Tuple[Dict[str, KeyInfo], Dict[int, Key], List[str]]:
        """This method reads the given keyboard layout, and extract useful data
        structures from this (to be used later by other methods). This
        basically builds the LayoutHelper class (and should be used only inside
        the constructor).

        Note:
            The given keyboard layout contains 24 layers. Each key appears in
            one (or several) layer of the keyboard. Accents are associated to
            the same key as their non-accented version.
            This class may be used to generate typing noise, so accents should
            have their own keys (and closer accents should be represented by
            closer keys). This method takes care of it, by generating "virtual
            keyboard layers", for each group of accents. The goal is to
            generate a virtual keyboard layer that is as close as possible as
            the actual keyboard, used by real-users.

        Args:
            keyboard_layout (Dict): Dictionary representing the keyboard and
                its layout.
            ignore_layers_after (Optional[int]) : Ignore higher layers of the
                keyboard layout. If `None` is given, no layer is ignored.

        Returns:
            Key information for each character in the keyboard.
            Key information for each layer of the keyboard.
            List of accents used in the keyboard.
        """
        keys_info = {}  # Dict char -> key infos (bounds, center, klayer ID)
        klayers_info = defaultdict(list)  # Dict klayer ID -> list of keys (bounds, char)
        all_accents = set()

        # A keyboard layout is made of several "layers", each identified by a KeyboardID
        last_klayer_id = len(keyboard_layout)
        for klayer in keyboard_layout:
            if klayer["buttons"] is None or (ignore_layers_after is not None and klayer["id"] > ignore_layers_after):
                continue

            # Each layer is a list of button
            for button in klayer["buttons"]:
                # Button always have a character, and optionally accents
                char, accents = button["labels"][0], button["labels"][1:]

                # Special characters : space, shift, numbers, magic, etc...
                if button["type"] != 1:
                    if char.lower() == SPACE:
                        char = " "
                    elif char == POINT:
                        # Points should be added to our key infos
                        pass
                    else:
                        # Other special characters are ignored
                        continue

                # Save the character and its key information
                # Save it only if it's not already in a previous klayer
                if char not in keys_info or keys_info[char].klayer_id > klayer["id"]:
                    keys_info[char] = KeyInfo(
                        klayer["id"],
                        button["boundingRect"]["right"] - button["boundingRect"]["left"],
                        button["boundingRect"]["bottom"] - button["boundingRect"]["top"],
                        (button["centerPoint"]["x"], button["centerPoint"]["y"]),
                    )
                # But always save its info in the klayers info
                klayers_info[klayer["id"]].append(Key(char, button["boundingRect"]))

                # Then, save the accents if any
                for i, char_accent in enumerate(accents):
                    all_accents.add(char_accent)

                    # Create a virtual position for the accent
                    bounds, center = self._make_virtual_key(i, button["boundingRect"])

                    # Save the accent (only if not existing) in a new virtual klayer
                    if char_accent not in keys_info:
                        keys_info[char_accent] = KeyInfo(
                            last_klayer_id,
                            bounds["right"] - bounds["left"],
                            bounds["bottom"] - bounds["top"],
                            (center["x"], center["y"]),
                        )
                    # But always saveits info in the klayers info
                    klayers_info[last_klayer_id].append(Key(char_accent, bounds))

                # If we added some accent in a virtual klayer, don't forget to update the last klayer ID
                if accents:
                    last_klayer_id += 1

        return keys_info, klayers_info, sorted(all_accents)

    def _make_virtual_key(
        self, idx: int, initial_bounds: Dict[str, float]
    ) -> Tuple[Dict[str, float], Dict[str, float]]:
        """Method to create a new boundary for an accented character. Based on
        the given id, the generated boundary box will be generated at a
        different position.

        This method tries to follow a similar pattern as the sample app, with
        accents appearing in lines of 4 accents.

        Args:
            idx (int): The index of the bounding box to generate.
            initial_bounds (Dict[str, float]): The bounding box of the
                non-accented key.

        Returns:
            Generated bounding box.
            Its associated center position.
        """
        width = initial_bounds["right"] - initial_bounds["left"]
        height = initial_bounds["bottom"] - initial_bounds["top"]

        start_x = initial_bounds["left"] + (idx % N_ACCENT_PER_LINE) * width
        start_y = initial_bounds["bottom"] - (idx // N_ACCENT_PER_LINE) * height

        bounds = {
            "bottom": start_y,
            "left": start_x,
            "right": start_x + width,
            "top": start_y - height,
        }
        center = {
            "x": bounds["left"] + width / 2,
            "y": bounds["top"] + height / 2,
        }
        return bounds, center

    def get_key_info(self, char: str) -> Tuple[float, float, float, float, int]:
        """Method to retrieve the information associated to a specific key.

        Args:
            char (str): Character for which to retrieve key information.

        Raises:
            KeyError: Exception raised if the given character can't be typed (
                because it doesn't exist on this keyboard layout).

        Returns:
            Width of the key for the requested character.
            Height of the key for the requested character.
            Center position (x-axis) of the key for the requested character.
            Center position (y-axis) of the key for the requested character.
            Keyboard layer ID where the character's key is located.
        """
        k = self.keys_info[char]
        return k.width, k.height, k.center[0], k.center[1], k.klayer_id

    def get_key(self, pos: Tuple[float, float], klayer_id: int) -> str:
        """Get the character associated with the given position.

        Args:
            pos (Tuple[float, float]): Position (x, y) in the keyboard.
            klayer_id (int): Keyboard layer ID to use.

        Returns:
            Character associated to the given position.
        """
        klayer = self.klayers_info[klayer_id]

        try:
            # Retrieve the key that contains the sampled position
            key = next(
                k
                for k in klayer
                if k.bounds["left"] <= pos[0] <= k.bounds["right"] and k.bounds["top"] <= pos[1] <= k.bounds["bottom"]
            )
        except StopIteration:
            # Maybe the sampled position was out of bound -> retrieve the closest key
            key = min(
                klayer,
                key=lambda k: euclidian_dist(
                    pos,
                    (
                        k.bounds["left"] + (k.bounds["right"] - k.bounds["left"]) / 2,
                        k.bounds["top"] + (k.bounds["bottom"] - k.bounds["top"]) / 2,
                    ),
                ),
            )

        return key.char
