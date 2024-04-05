"""Module containing the code necessary to interact with the emulators, using
Appium.
"""

import html
import io
import json
import random
import subprocess
import time
from typing import Callable, Dict, List, Tuple

import cv2
import numpy as np
import pytesseract
import regex as re
from appium import webdriver
from PIL import Image
from selenium.common.exceptions import StaleElementReferenceException
from selenium.webdriver import ActionChains
from selenium.webdriver.common.actions import interaction
from selenium.webdriver.common.actions.action_builder import ActionBuilder
from selenium.webdriver.common.actions.pointer_input import PointerInput
from selenium.webdriver.common.by import By
from selenium.webdriver.remote.webelement import WebElement


ANDROID = "android"
IOS = "ios"
GBOARD = "gboard"
TAPPA = "tappa"
FLEKSY = "fleksy"
ANDROID_CAPABILITIES = {
    "platformName": "android",
    "automationName": "UiAutomator2",
    "enableMultiWindows": True,
    "deviceName": "test",
    "newCommandTimeout": 3600,
}
IOS_CAPABILITIES = {
    "platformName": "iOS",
    "automationName": "XCUITest",
    "udid": "auto",
    "xcodeOrgId": "8556JTA4X4",
    "xcodeSigningId": "iPhone Developer",
    "useNewWDA": False,
    "usePrebuiltWdDA": True,
    "startIWDP": True,
    "bundleId": "com.apple.MobileSMS",
    "newCommandTimeout": 3600,
}
BROWSER_PAD_URL = "https://www.justnotepad.com"
ANDROID_TYPING_FIELD_CLASS_NAME = "android.widget.EditText"
DUMMY_RECIPIENT = "0"
IOS_TYPING_FIELD_ID = "messageBodyField"
IOS_START_CHAT_CLASS_NAME = "XCUIElementTypeCell"
TESSERACT_CONFIG = "-c tessedit_char_blacklist=0123456789”:!@·$%&/()=.¿?"
PREDICTION_DELAY = 0.4
CONTENT_TO_IGNORE = ["Sticker", "GIF", "Clipboard", "Settings", "Back", "Switch input method", "Paste item"]
CONTENT_TO_RENAME = {
    "Shift": "shift",
    "Delete": "backspace",
    "Space": "spacebar",
    "space": "spacebar",
    "Emoji button": "smiley",
    "Emoji": "smiley",
    "Search": "enter",
    "Symbol keyboard": "numbers",
    "Symbols": "numbers",
    "Voice input": "mic",
    "Close features menu": "magic",
    "Open features menu": "magic",
    "underline": "_",
    "&amp;": "&",
    "ampersand": "&",
    "Dash": "-",
    "Plus": "+",
    "Left parenthesis": "(",
    "Right parenthesis": ")",
    "slash": "/",
    "Apostrophe": "'",
    "Colon": ":",
    "Semicolon": ";",
    "Exclamation": "!",
    "Question mark": "?",
    "Letter keyboard": "letters",
    "Letters": "letters",
    "Digit keyboard": "numbers",
    "More symbols": "shift",
    "Capital I": "I",
}
FLEKSY_LAYOUT = {
    "keyboard_frame": [0, 1035, 1080, 730],
    "suggestions_frames": [
        [132, 16, 300, 88],
        [445, 16, 300, 88],
        [758, 16, 300, 88],
    ],
    "lowercase": {
        "q": [8, 134, 95, 120],
        "w": [113, 134, 95, 120],
        "e": [221, 134, 95, 120],
        "r": [329, 134, 95, 120],
        "t": [437, 134, 95, 120],
        "y": [545, 134, 95, 120],
        "u": [653, 134, 95, 120],
        "i": [761, 134, 95, 120],
        "o": [869, 134, 95, 120],
        "p": [977, 134, 95, 120],
        "a": [62, 278, 95, 120],
        "s": [168, 278, 95, 120],
        "d": [276, 278, 95, 120],
        "f": [383, 278, 95, 120],
        "g": [491, 278, 95, 120],
        "h": [599, 278, 95, 120],
        "j": [707, 278, 95, 120],
        "k": [815, 278, 95, 120],
        "l": [924, 278, 95, 120],
        "shift": [8, 423, 147, 120],
        "z": [168, 423, 95, 120],
        "x": [276, 423, 95, 120],
        "c": [383, 423, 95, 120],
        "v": [491, 423, 95, 120],
        "b": [599, 423, 95, 120],
        "n": [707, 423, 95, 120],
        "m": [815, 423, 95, 120],
        "backspace": [924, 423, 147, 120],
        "numbers": [8, 568, 135, 120],
        "magic": [17, 20, 90, 85],
        "smiley": [155, 568, 111, 120],
        "spacebar": [276, 568, 526, 120],
        ".": [815, 568, 108, 120],
        "enter": [934, 568, 140, 120],
    },
    "uppercase": {
        "Q": [8, 134, 95, 120],
        "W": [113, 134, 95, 120],
        "E": [221, 134, 95, 120],
        "R": [329, 134, 95, 120],
        "T": [437, 134, 95, 120],
        "Y": [545, 134, 95, 120],
        "U": [653, 134, 95, 120],
        "I": [761, 134, 95, 120],
        "O": [869, 134, 95, 120],
        "P": [977, 134, 95, 120],
        "A": [62, 278, 95, 120],
        "S": [168, 278, 95, 120],
        "D": [276, 278, 95, 120],
        "F": [383, 278, 95, 120],
        "G": [491, 278, 95, 120],
        "H": [599, 278, 95, 120],
        "J": [707, 278, 95, 120],
        "K": [815, 278, 95, 120],
        "L": [924, 278, 95, 120],
        "shift": [8, 423, 147, 120],
        "Z": [168, 423, 95, 120],
        "X": [276, 423, 95, 120],
        "C": [383, 423, 95, 120],
        "V": [491, 423, 95, 120],
        "B": [599, 423, 95, 120],
        "N": [707, 423, 95, 120],
        "M": [815, 423, 95, 120],
        "backspace": [924, 423, 147, 120],
        "numbers": [8, 568, 135, 120],
        "magic": [17, 20, 90, 85],
        "smiley": [155, 568, 111, 120],
        "spacebar": [276, 568, 526, 120],
        ".": [815, 568, 108, 120],
        "enter": [934, 568, 140, 120],
    },
    "numbers": {
        "1": [8, 134, 95, 120],
        "2": [113, 134, 95, 120],
        "3": [221, 134, 95, 120],
        "4": [329, 134, 95, 120],
        "5": [437, 134, 95, 120],
        "6": [545, 134, 95, 120],
        "7": [653, 134, 95, 120],
        "8": [761, 134, 95, 120],
        "9": [869, 134, 95, 120],
        "0": [977, 134, 95, 120],
        "@": [8, 278, 95, 120],
        "#": [113, 278, 95, 120],
        "$": [221, 278, 95, 120],
        "_": [329, 278, 95, 120],
        "&": [437, 278, 95, 120],
        "-": [545, 278, 95, 120],
        "+": [653, 278, 95, 120],
        "(": [761, 278, 95, 120],
        ")": [869, 278, 95, 120],
        "/": [977, 278, 95, 120],
        "shift": [8, 423, 115, 120],
        "*": [136, 423, 77, 120],
        '"': [227, 423, 77, 120],
        "'": [318, 423, 77, 120],
        ":": [409, 423, 77, 120],
        ";": [500, 423, 77, 120],
        ",": [591, 423, 77, 120],
        "!": [773, 423, 77, 120],
        "?": [864, 423, 77, 120],
        "backspace": [956, 423, 115, 120],
        "letters": [8, 568, 135, 120],
        "magic": [17, 20, 90, 85],
        "mic": [155, 568, 111, 120],
        "spacebar": [276, 568, 526, 120],
        ".": [815, 568, 108, 120],
        "enter": [934, 568, 140, 120],
    },
}


class Emulator:
    """Class used to interact with an emulator and type word on a given keyboard.

    Args:
        platform (str): `android` or `ios`.
        keyboard (str): The name of the keyboard installed on the emulator.
            This is needed because each keyboard has a different layout, and we
            need to know each key's position in order to type words.
        device (str, optional): Device UDID to use.
        host (str, optional): Appium server's address.
        port (str, optional): Appium server's port.

    Raises:
        ValueError: Error raised if the given platform doesn't exist.
    """

    def __init__(
        self,
        platform: str,
        keyboard: str,
        device: str = None,
        host: str = "127.0.0.1",
        port: str = "4723",
        ios_name: str = None,
        ios_platform: str = None,
    ):
        super().__init__()

        self.platform = platform.lower()
        if self.platform not in [ANDROID, IOS]:
            raise ValueError(f"Unknown platform : {self.platform}. Please specify `{ANDROID}` or `{IOS}`.")

        # Start appium
        capabilities = ANDROID_CAPABILITIES if self.platform == ANDROID else IOS_CAPABILITIES
        if self.platform == IOS:
            capabilities["deviceName"] = ios_name
            capabilities["platformVersion"] = ios_platform
            capabilities["wdaLocalPort"] = 8000 + device
        if self.platform == ANDROID and device is not None:
            capabilities["udid"] = device
        self.driver = webdriver.Remote(f"{host}:{port}", capabilities)
        self.driver.implicitly_wait(20)

        self.screen_size = self.driver.get_window_size()

        self.keyboard = keyboard.lower()

        # Access a typing field
        self.typing_field = None
        self._access_typing_field()

        # Keep track of the keyboard behavior
        # When the typing field is empty, the keyboard is uppercase by default
        self.kb_is_upper = True
        self.last_char_is_space = False
        self.last_char_is_eos = False

        # Get the right layout
        if self.keyboard == GBOARD:
            self.detected = GboardLayoutDetector(self.driver, self._tap)
            self.layout = self.detected.layout
        elif self.keyboard == TAPPA:
            self.detected = TappaLayoutDetector(self.driver, self._tap)
            self.layout = self.detected.layout
        elif self.keyboard == FLEKSY:
            self.layout = FLEKSY_LAYOUT
        elif self.keyboard == IOS:
            self.detected = IosLayoutDetector(self.driver, self._tap)
            self.layout = self.detected.layout
        else:
            raise ValueError(
                f"Unknown keyboard : {self.keyboard}. Please specify `{GBOARD}`, `{TAPPA}`, " f"`{FLEKSY}` or `{IOS}`."
            )

        self.typing_field.clear()

    def _access_typing_field(self):
        """Start the right application and access the typing field where we
        will type our text.
        """
        if self.platform == ANDROID:
            subprocess.run(
                ["adb", "shell", "am", "start", "-a", "android.intent.action.VIEW", "-d", BROWSER_PAD_URL],
                stdout=subprocess.PIPE,
            )
            typing_field_loaded = False
            while not typing_field_loaded:
                typing_fields = self.driver.find_elements(By.CLASS_NAME, ANDROID_TYPING_FIELD_CLASS_NAME)
                typing_field_loaded = len(typing_fields) == 2
            self.typing_field = typing_fields[0]
        else:
            self.driver.find_element(By.CLASS_NAME, IOS_START_CHAT_CLASS_NAME).click()
            self.typing_field = self.driver.find_element(By.ID, IOS_TYPING_FIELD_ID)
        self.typing_field.click()
        self.typing_field.clear()

    def get_android_devices() -> List[str]:
        """Static method that uses the `adb devices` command to retrieve the
        list of devices running.

        Returns:
            List of detected device UDID.
        """
        result = subprocess.run(["adb", "devices"], stdout=subprocess.PIPE)
        devices = result.stdout.decode().split("\n")
        devices = [d.split()[0] for d in devices if not (d.startswith("List of devices attached") or len(d) == 0)]
        return devices

    def get_ios_devices() -> List[Tuple[str, str]]:
        """Static method that uses the `xcrun simctl` command to retrieve the
        list of booted devices.

        Returns:
            List of booted device platform and device name.
        """
        devices = []

        result = subprocess.run(["xcrun", "simctl", "list", "devices"], stdout=subprocess.PIPE)
        out = result.stdout.decode().split("\n")

        curr_platform = ""
        for line in out:
            if line.startswith("== ") and line.endswith(" =="):
                continue
            elif line.startswith("-- ") and line.endswith(" --"):
                curr_platform = line[3:-3]
            else:
                m = re.match(r"\s+([^\t]+)\s+\([A-Z0-9\-]+\)\s+\((Booted|Shutdown)\)", line)
                if m:
                    device_name = m.group(1)
                    status = m.group(2)

                    if status == "Booted" and curr_platform.startswith("iOS "):
                        devices.append((curr_platform[4:], device_name))

        return devices

    def _paste(self, text: str):
        """Paste the given text into the typing field, to quickly simulate
        typing a context.

        Args:
            text (str): Text to paste.
        """
        if text == "":
            self.typing_field.clear()
            self.kb_is_upper = True
            self.last_char_is_space = False
            self.last_char_is_eos = False
        else:
            # Note : on Android, pasting content in the field will erase the previous content
            # (which is what we want). On iOS it will not, we need to do it "manually"
            if self.keyboard == IOS:
                self.typing_field.clear()
            self.typing_field.send_keys(text)
            self.kb_is_upper = len(text) > 1 and self._is_eos(text[-2]) and text.endswith(" ")
            self.last_char_is_space = text.endswith(" ")
            self.last_char_is_eos = self._is_eos(text[-1])

    def paste(self, text: str):
        """Paste the given text into the typing field, to quickly simulate
        typing a context.

        This method is just a wrapper around `_paste()`, making sure the typing
        field is accessible. If for some reason it is not accessible, it tries
        to access it and perform the action again.

        Args:
            text (str): Text to paste.
        """
        try:
            self._paste(text)
        except StaleElementReferenceException:
            self._access_typing_field()
            self._paste(text)

    def type_characters(self, characters: str):  # noqa: C901
        """Type the given sentence on the keyboard. For each character, it
        finds the keys to press and send a tap on the keyboard.

        Args:
            characters (str): The sentence to type.
        """
        for c in characters:
            if c == " ":
                if self.last_char_is_space:
                    # If the previous character was a space, don't retype a space
                    # because it can be transformed into a `.`
                    continue

                if self.kb_is_upper:
                    self._tap(self.layout["uppercase"]["spacebar"])
                else:
                    self._tap(self.layout["lowercase"]["spacebar"])

                # Behavior of the keyboard : if the previous character typed was an EOS marker
                # and a space is typed, the keyboard automatically switch to uppercase
                if self.last_char_is_eos:
                    self.kb_is_upper = True
            elif c in self.layout["lowercase"]:
                # The character is a lowercase character
                if self.kb_is_upper:
                    # If the keyboard is in uppercase mode, change it to lowercase
                    self._tap(self.layout["uppercase"]["shift"])
                self._tap(self.layout["lowercase"][c])
            elif c in self.layout["uppercase"]:
                # The character is an uppercase character
                if not self.kb_is_upper:
                    # Change the keyboard to uppercase
                    self._tap(self.layout["lowercase"]["shift"])
                self._tap(self.layout["uppercase"][c])
                # After typing one character, the keyboard automatically come back to lowercase
            elif c in self.layout["numbers"]:
                # The character is a number of a special character
                # Access the number keyboard properly
                if self.kb_is_upper:
                    self._tap(self.layout["uppercase"]["numbers"])
                else:
                    self._tap(self.layout["lowercase"]["numbers"])
                self._tap(self.layout["numbers"][c])

                if c != "'" or self.keyboard == GBOARD:
                    # For some reason, when `'` is typed, the keyboard automatically goes back
                    # to lowercase, so no need to re-tap the button (unless the keyboard is GBoard).
                    # In all other cases, switch back to letters keyboard
                    self._tap(self.layout["numbers"]["letters"])
            else:
                # Can't type this character, ignore it
                continue

            # Behavior of the keyboard : if the previous character typed was an EOS marker
            # and a space is typed, the keyboard automatically switch to uppercase
            self.kb_is_upper = self.last_char_is_eos and c == " "

            # Update infos about what we typed
            self.last_char_is_eos = self._is_eos(c)
            self.last_char_is_space = c == " "

    def _is_eos(self, c: str) -> bool:
        """Check if the given character is an End-Of-Sentence marker. If an EOS
        marker is typed followed by a space, the keyboard automatically switch
        to uppercase letters (unless it's GBoard).

        Args:
            c (str): Character to check.

        Returns:
            True if the character is an EOS marker.
        """
        if self.keyboard == GBOARD:
            return False
        else:
            return c in [".", "!", "?"]

    def _tap(self, frame: List[int], keyboard_frame: List[int] = None):
        """Tap on the screen at the position described by the given frame.

        Args:
            frame (List[int]): Frame describing the position where to tap. A
                frame is : [start_pos_x, start_pos_y, width, height].
            keyboard_frame (List[int]): If specified, the Keyboard frame to
                use. If `None`, it will use `self.layout["keyboard_frame"]`.
        """
        x, y, w, h = frame
        base_x, base_y, *_ = keyboard_frame if keyboard_frame else self.layout["keyboard_frame"]

        pos_x = base_x + x + int(w / 2)
        pos_y = base_y + y + int(h / 2)

        actions = ActionChains(self.driver)
        actions.w3c_actions = ActionBuilder(self.driver, mouse=PointerInput(interaction.POINTER_TOUCH, "touch"))
        actions.w3c_actions.pointer_action.move_to_location(pos_x, pos_y)
        actions.w3c_actions.pointer_action.pointer_down()
        actions.w3c_actions.pointer_action.pause(0.05)
        actions.w3c_actions.pointer_action.release()
        actions.perform()

    def _take_screenshot(self):
        """Take a screenshot of the full screen.

        Returns:
            The image of the screen.
        """
        screen_data = self.driver.get_screenshot_as_png()
        screen = np.asarray(Image.open(io.BytesIO(screen_data)))
        return cv2.resize(
            screen, (self.screen_size["width"], self.screen_size["height"]), interpolation=cv2.INTER_AREA
        )

    def get_predictions(self, lang: str = "en") -> List[str]:
        """Retrieve the predictions displayed by the keyboard.

        Args:
            lang (str): Language to use for the OCR.

        Returns:
            List of predictions from the keyboard.
        """
        if hasattr(self, "detected"):
            # Only keyboards that were auto-detected (using XML tree) have the
            # attribute `detected`. If that's the case, it means we
            # can retrieve the suggestions directly from the XML tree !
            predictions = self.detected.get_suggestions()
        else:
            # Other keyboards still have to use (slow) OCR
            time.sleep(PREDICTION_DELAY)
            screen = self._take_screenshot()

            kb_x, kb_y, kb_w, kb_h = self.layout["keyboard_frame"]
            screen = screen[kb_y : kb_y + kb_h, kb_x : kb_x + kb_w]

            predictions = []
            for x, y, w, h in self.layout["suggestions_frames"]:
                suggestion_area = screen[y : y + h, x : x + w]
                ocr_results = pytesseract.image_to_string(suggestion_area, config=TESSERACT_CONFIG)
                pred = ocr_results.strip().replace("“", "").replace('"', "").replace("\\", "")
                predictions.append(pred)

        return predictions

    def _get_text(self) -> str:
        """Return the text currently contained in the typing field.

        Returns:
            Text of the typing field.
        """
        return self.typing_field.text

    def get_text(self) -> str:
        """Return the text currently contained in the typing field.

        This method is just a wrapper around `_get_text()`, making sure the
        typing field is accessible. If for some reason it is not accessible, it
        tries to access it and perform the action again.

        Returns:
            Text of the typing field.
        """
        try:
            return self._get_text()
        except StaleElementReferenceException:
            self._access_typing_field()
            return self._get_text()

    def show_keyboards(self):
        """Take a screenshot and overlay the given layout, for debugging the
        position of each keys.
        """
        # Type a character, in order to have some suggestions
        # Keyboard starts with uppercase letter by default (unless GBoard), and
        # automatically go to lowercase after
        if self.keyboard == GBOARD:
            self._tap(self.layout["lowercase"]["a"])
        else:
            self._tap(self.layout["uppercase"]["A"])
        screen_lower = self._take_screenshot()

        self._tap(self.layout["lowercase"]["shift"])
        screen_upper = self._take_screenshot()

        self._tap(self.layout["lowercase"]["numbers"])
        screen_numbers = self._take_screenshot()

        for layout_name, screen in zip(
            ["lowercase", "uppercase", "numbers"], [screen_lower, screen_upper, screen_numbers]
        ):
            self._set_area_box(screen, (0, 0), self.layout["keyboard_frame"], "keyboard frame")
            if "suggestions_frames" in self.layout:
                for i, suggestion_frame in enumerate(self.layout["suggestions_frames"]):
                    self._set_area_box(screen, self.layout["keyboard_frame"], suggestion_frame, f"suggestion {i}")
            for key_name, key_frame in self.layout[layout_name].items():
                self._set_area_box(screen, self.layout["keyboard_frame"], key_frame, key_name)

            cv2.imshow(layout_name, screen)

        cv2.waitKey(0)
        cv2.destroyAllWindows()

    def _set_area_box(self, image, base_coords: Tuple[int], coords: Tuple[int], tag: str):
        """Add an area box on the given image (color is random).

        Args:
            image: Image where to add the box.
            base_coords (Tuple[int]): Base coordinates from the full image.
            coords (Tuple[int]): Coordinates of the element, as well as
                dimensions.
            tag (str): Tag for this box.
        """
        base_x, base_y, *_ = base_coords
        x, y, w, h = coords
        x += base_x
        y += base_y
        # Generate color only until 200, to ensure it's dark enough
        color = (random.randint(0, 200), random.randint(0, 200), random.randint(0, 200))
        cv2.rectangle(image, (x, y), (x + w, y + h), color, 2)
        cv2.putText(image, tag, (x, y + h + 17), cv2.FONT_HERSHEY_SIMPLEX, 0.5, color, 2)


class LayoutDetector:
    """Base class for auto-detection of the keyboard layout.

    To auto-detect a new keyboard, create a new sub-class, and overwite
    `__init__()` and `get_suggestions()`. Use the existing subclass for GBoard
    as reference.

    Args:
        driver (webdriver.Remote): The Appium driver, used to access elements
            on the emulator.
        tap_fn (Callable): A callback used to tap at specific position on the
            screen. See `Emulator._tap()`.
        xpath_root (str): XPath to the root element of the keyboard.
        xpath_keys (str): XPath to detect the keys elements.
    """

    def __init__(
        self, driver: webdriver.Remote, tap_fn: Callable, xpath_root: str, xpath_keys: str, android: bool = True
    ):
        self.driver = driver
        self.tap = tap_fn
        self.xpath_root = xpath_root
        self.xpath_keys = xpath_keys
        self.android = android

        layout = {}

        # Get the root element of our keyboard
        root = self.driver.find_element(By.XPATH, self.xpath_root)

        # On empty field, the keyboard is on uppercase
        # So first, retrieve the keyboard frame and uppercase characters
        kb_frame, screen_layout = self._detect_keys(root, current_layout="uppercase")
        layout["keyboard_frame"] = kb_frame
        layout["uppercase"] = screen_layout

        # Then, after typing a letter, the keyboard goes to lowercase automatically
        self.tap(layout["uppercase"]["A"], layout["keyboard_frame"])
        _, screen_layout = self._detect_keys(root, keyboard_frame=layout["keyboard_frame"], current_layout="lowercase")
        layout["lowercase"] = screen_layout

        # Finally, access the symbols keyboard and get characters positions
        self.tap(layout["lowercase"]["numbers"], layout["keyboard_frame"])
        _, screen_layout = self._detect_keys(root, keyboard_frame=layout["keyboard_frame"], current_layout="numbers")
        layout["numbers"] = screen_layout

        # Reset out keyboard to the original layer
        self.tap(layout["numbers"]["letters"], layout["keyboard_frame"])

        # Fix the keys' offset compared to the keyboard frame
        if self.android:
            self.layout = self._apply_status_bar_offset(layout)
        else:
            self.layout = layout

    def get_suggestions(self) -> List[str]:
        """Method to retrieve the keyboard suggestions from the XML tree.

        Note that it's slower to access the XML through methods like
        `find_element()`, and it's faster to access the raw XML with
        `self.driver.page_source` and parse it as text directly.

        Raises:
            NotImplementedError: Exception raised if this method is not
                overwritten.

        Returns:
            List of suggestions from the keyboard.
        """
        raise NotImplementedError

    def _detect_keys(
        self, root: WebElement, current_layout: str, keyboard_frame: List[int] = None
    ) -> Tuple[List[int], Dict]:
        """This method detects all keys currently on screen.

        If no keyboard_frame is given, it will also detects the keyboard frame.

        Args:
            root (WebElement): Root element in the XML tree that represents the
                keyboard (with all its keys).
            current_layout (str): Name of the current layout.
            keyboard_frame (List[int], optional): Optionally, the keyboard
                frame (so we don't need to re-detect it everytime).

        Returns:
            Keyboard frame
            Layout with all the keys detected on this screen.
        """
        layout = {}
        if keyboard_frame is None:
            if self.android:
                # Detect the keyboard frame
                kb = root.find_element(By.ID, "android:id/inputArea")
                keyboard_frame = self._get_frame(kb)
            else:
                keyboard_frame = self._get_frame(root)

        for key_elem in root.find_elements(By.XPATH, self.xpath_keys):
            label = self._get_label(key_elem, current_layout=current_layout)
            if label is not None:
                layout[label] = self._get_frame(key_elem)

        # Then update the letters positions to be relative to the keyboard frame
        for k in layout:
            layout[k][0] -= keyboard_frame[0]
            layout[k][1] -= keyboard_frame[1]

        return keyboard_frame, layout

    def _get_frame(self, element: WebElement) -> List[int]:
        """For layout detection, this method returns the bounds of the given
        element.

        Args:
            element (WebElement): XML Element describing a key.

        Returns:
            Bounds of this key.
        """
        if self.android:
            m = re.match(r"\[(\d+),(\d+)\]\[(\d+),(\d+)\]", element.get_attribute("bounds"))
            if m:
                bounds = [int(g) for g in m.groups()]
                return [bounds[0], bounds[1], bounds[2] - bounds[0], bounds[3] - bounds[1]]
        else:
            r = json.loads(element.get_attribute("rect"))
            return [r["x"], r["y"], r["width"], r["height"]]

    def _get_label(self, element: WebElement, current_layout: str, is_suggestion: bool = False) -> str:
        """For layout detection, this method returns the content of the given
        element.

        This method returns `None` if it's a key we don't care about. This
        method takes care of translating the content (the name used in the XML
        tree is not the same as the one used in our layout).

        Args:
            element (WebElement): XML Element describing a key.
            current_layout (str): Name of the current layout.
            is_suggestion (bool, optional): If we are retrieving the content of
                a suggestion, the content shouldn't be translated.

        Returns:
            Content of the key, or None if it's a key we should ignore.
        """
        content = element.get_attribute("content-desc") if self.android else element.get_attribute("name")

        if is_suggestion:
            # If we are getting the content of the suggestion, return the content directly
            return content

        if content in CONTENT_TO_IGNORE:
            return None
        elif not self.android and content == "more":
            if current_layout == "uppercase" or current_layout == "lowercase":
                return "numbers"
            else:
                return "letters"
        elif content in CONTENT_TO_RENAME:
            return CONTENT_TO_RENAME[content]
        else:
            return content

    def _get_status_bar_bounds(self) -> List[int]:
        """For layout detection, this method retrieve the bounds of the status
        bar from the XML tree.

        Returns:
            Bounds of the status bar.
        """
        sb = self.driver.find_element(By.ID, "com.android.systemui:id/status_bar")
        return self._get_frame(sb)

    def _apply_status_bar_offset(self, layout: Dict) -> Dict:
        """Method offsetting the given layout to match the screen.

        On Android, somehow the detected positions for the keys aren't matching
        what we see on screen. This is because of the status bar, which shift
        everything. So, detect the status bar, and shift back the keys to the
        right position.

        Args:
            layout (Dict): Layout to fix.

        Returns:
            Fixed layout.
        """
        sb_bounds = self._get_status_bar_bounds()
        dy = sb_bounds[3]
        screen_size = layout["keyboard_frame"][1] + layout["keyboard_frame"][3]

        # First of all, offset the keyboard frame
        frame_dy1 = int(dy * (layout["keyboard_frame"][1] / screen_size))
        frame_dy2 = int(dy * ((layout["keyboard_frame"][1] + layout["keyboard_frame"][3]) / screen_size))
        layout["keyboard_frame"][1] -= frame_dy1
        layout["keyboard_frame"][3] -= frame_dy2 - frame_dy1

        # Then do the same for each keys of each layouts
        for layer in ["lowercase", "uppercase", "numbers"]:
            for k in layout[layer]:
                dy1 = int(dy * ((layout["keyboard_frame"][1] + layout[layer][k][1]) / screen_size))
                dy2 = int(
                    dy * ((layout["keyboard_frame"][1] + layout[layer][k][1] + layout[layer][k][3]) / screen_size)
                )
                layout[layer][k][1] -= dy1 - frame_dy1
                layout[layer][k][3] -= dy2 - dy1

        return layout


class GboardLayoutDetector(LayoutDetector):
    """Layout detector for the Gboard keyboard. See `LayoutDetector` for more
    information.
    """

    def __init__(self, *args, **kwargs):
        super().__init__(
            *args,
            xpath_root="./*/*[@package='com.google.android.inputmethod.latin']",
            xpath_keys=".//*[@resource-id][@content-desc]",
            **kwargs,
        )

    def get_suggestions(self) -> List[str]:
        """Method to retrieve the keyboard suggestions from the XML tree.

        Returns:
            List of suggestions from the keyboard.
        """
        suggestions = []

        sections = [
            data
            for data in self.driver.page_source.split("<android.widget.FrameLayout")
            if "com.google.android.inputmethod" in data
        ]
        for section in sections:
            if "content-desc" in section and "resource-id" not in section and 'long-clickable="true"' in section:
                m = re.search(r"content\-desc=\"([^\"]*)\"", section)
                if m:
                    content = m.group(1)

                    # Deal with emojis
                    emoji = re.match(r"emoji (&[^;]+;)", content)
                    suggestions.append(html.unescape(emoji[1]) if emoji else content)

        return suggestions


class IosLayoutDetector(LayoutDetector):
    """Layout detector for the iOS default keyboard. See `LayoutDetector` for
    more information.
    """

    def __init__(self, *args, **kwargs):
        super().__init__(
            *args,
            xpath_root=".//XCUIElementTypeKeyboard",
            xpath_keys="(.//XCUIElementTypeKey|.//XCUIElementTypeButton)",
            android=False,
            **kwargs,
        )

    def get_suggestions(self) -> List[str]:
        """Method to retrieve the keyboard suggestions from the XML tree.

        Returns:
            List of suggestions from the keyboard.
        """
        suggestions = []

        sections = [
            data for data in self.driver.page_source.split("<XCUIElementTypeOther") if "name=" in data.split(">")[0]
        ]
        is_typing_predictions_section = False
        for section in sections:
            m = re.search(r"name=\"([^\"]*)\"", section)
            if m:
                name = m.group(1)

                if name == "Typing Predictions":
                    is_typing_predictions_section = True
                    continue

                if is_typing_predictions_section:
                    suggestions.append(name.replace("“", "").replace("”", ""))

        return suggestions


class TappaLayoutDetector(LayoutDetector):
    """Layout detector for the Tappa keyboard. See `LayoutDetector` for more
    information.
    """

    def __init__(self, *args, **kwargs):
        super().__init__(
            *args,
            xpath_root="./*/*[@package='com.tappa.keyboard']",
            xpath_keys=".//com.mocha.keyboard.inputmethod.keyboard.Key",
            **kwargs,
        )

    def get_suggestions(self) -> List[str]:
        """Method to retrieve the keyboard suggestions from the XML tree.

        Returns:
            List of suggestions from the keyboard.
        """
        suggestions = []

        # Get the raw content as text, weed out useless elements
        section = self.driver.page_source.split("com.tappa.keyboard:id/toolbar")[1].split(
            "</android.widget.FrameLayout>"
        )[0]

        for line in section.split("\n"):
            if "<android.widget.TextView" in line:
                m = re.search(r"text=\"([^\"]*)\"", line)
                if m:
                    suggestions.append(html.unescape(m.group(1)))

        return suggestions
