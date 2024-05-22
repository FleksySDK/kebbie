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
KBKITPRO = "kbkitpro"
KBKITOSS = "kbkitoss"
SWIFTKEY = "swiftkey"
YANDEX = "yandex"
KEYBOARD_PACKAGE = {
    GBOARD: "com.google.android.inputmethod.latin",
    SWIFTKEY: "com.touchtype.swiftkey",
    YANDEX: "ru.yandex.androidkeyboard",
    TAPPA: "com.tappa.keyboard",
}
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
CONTENT_TO_IGNORE = [
    "Sticker",
    "GIF",
    "Clipboard",
    "Settings",
    "Back",
    "Switch input method",
    "Paste item",
    "Close",
    "paintpalette",
    "Search Document",
    "Microphone",
    "gearshape",
    "Next Locale",
    "paintpalette",
    "EmojiCategories/smileysAndPeople",
    "EmojiCategories/animalsAndNature",
    "EmojiCategories/foodAndDrink",
    "EmojiCategories/activity",
    "EmojiCategories/travelAndPlaces",
    "EmojiCategories/objects",
    "EmojiCategories/symbols",
    "EmojiCategories/flags",
    "Add",
    "And",
    "Are",
    "“A”",
    "🚀",
]
CONTENT_TO_RENAME = {
    "Shift": "shift",
    "Delete": "backspace",
    "Backspace": "backspace",
    "Space": "spacebar",
    "space": "spacebar",
    "Emoji button": "smiley",
    "Emoji": "smiley",
    "Keyboard Type - emojis": "smiley",
    "Search": "enter",
    "return": "enter",
    "Enter": "enter",
    "Symbol keyboard": "numbers",
    "Symbols": "numbers",
    "Symbols and numbers": "numbers",
    "Keyboard Type - numeric": "numbers",
    "Voice input": "mic",
    ",, alternatives available, Voice typing, long press to activate": "mic",
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
    "Keyboard Type - auto": "letters",
    "Digit keyboard": "numbers",
    "More symbols": "shift",
    "Keyboard Type - symbolic": "shift",
    "Double tap for uppercase": "shift",
    "Double tap for caps lock": "shift",
    "capital Q": "Q",
    "capital W": "W",
    "capital E": "E",
    "capital R": "R",
    "capital T": "T",
    "capital Y": "Y",
    "capital U": "U",
    "capital I": "I",
    "Capital I": "I",
    "capital O": "O",
    "capital P": "P",
    "capital A": "A",
    "capital S": "S",
    "capital D": "D",
    "capital F": "F",
    "capital G": "G",
    "capital H": "H",
    "capital J": "J",
    "capital K": "K",
    "capital L": "L",
    "capital Z": "Z",
    "capital X": "X",
    "capital C": "C",
    "capital V": "V",
    "capital B": "B",
    "capital N": "N",
    "capital M": "M",
}
FLEKSY_LAYOUT = {
    "keyboard_frame": [0, 517, 393, 266],  # Only the keyboard frame is defined as absolute position
    # The layout is then defined as relative position (to the keyboard frame)
    # so that if the device size change, we just have to adjust the keyboard
    # frame, and the rest should follow
    "lowercase": {
        "q": [0.007407407407407408, 0.19356164383561643, 0.08796296296296297, 0.1643835616438356],
        "w": [0.10462962962962963, 0.19356164383561643, 0.08796296296296297, 0.1643835616438356],
        "e": [0.20462962962962963, 0.19356164383561643, 0.08796296296296297, 0.1643835616438356],
        "r": [0.30462962962962964, 0.19356164383561643, 0.08796296296296297, 0.1643835616438356],
        "t": [0.4046296296296296, 0.19356164383561643, 0.08796296296296297, 0.1643835616438356],
        "y": [0.5046296296296297, 0.19356164383561643, 0.08796296296296297, 0.1643835616438356],
        "u": [0.6046296296296296, 0.19356164383561643, 0.08796296296296297, 0.1643835616438356],
        "i": [0.7046296296296296, 0.19356164383561643, 0.08796296296296297, 0.1643835616438356],
        "o": [0.8046296296296296, 0.19356164383561643, 0.08796296296296297, 0.1643835616438356],
        "p": [0.9046296296296297, 0.19356164383561643, 0.08796296296296297, 0.1643835616438356],
        "a": [0.05740740740740741, 0.40082191780821917, 0.08796296296296297, 0.1643835616438356],
        "s": [0.15555555555555556, 0.40082191780821917, 0.08796296296296297, 0.1643835616438356],
        "d": [0.25555555555555554, 0.40082191780821917, 0.08796296296296297, 0.1643835616438356],
        "f": [0.35462962962962963, 0.40082191780821917, 0.08796296296296297, 0.1643835616438356],
        "g": [0.4546296296296296, 0.40082191780821917, 0.08796296296296297, 0.1643835616438356],
        "h": [0.5546296296296296, 0.40082191780821917, 0.08796296296296297, 0.1643835616438356],
        "j": [0.6546296296296297, 0.40082191780821917, 0.08796296296296297, 0.1643835616438356],
        "k": [0.7546296296296297, 0.40082191780821917, 0.08796296296296297, 0.1643835616438356],
        "l": [0.8555555555555555, 0.40082191780821917, 0.08796296296296297, 0.1643835616438356],
        "shift": [0.007407407407407408, 0.5994520547945206, 0.1361111111111111, 0.1643835616438356],
        "z": [0.15555555555555556, 0.5994520547945206, 0.08796296296296297, 0.1643835616438356],
        "x": [0.25555555555555554, 0.5994520547945206, 0.08796296296296297, 0.1643835616438356],
        "c": [0.35462962962962963, 0.5994520547945206, 0.08796296296296297, 0.1643835616438356],
        "v": [0.4546296296296296, 0.5994520547945206, 0.08796296296296297, 0.1643835616438356],
        "b": [0.5546296296296296, 0.5994520547945206, 0.08796296296296297, 0.1643835616438356],
        "n": [0.6546296296296297, 0.5994520547945206, 0.08796296296296297, 0.1643835616438356],
        "m": [0.7546296296296297, 0.5994520547945206, 0.08796296296296297, 0.1643835616438356],
        "backspace": [0.8555555555555555, 0.5994520547945206, 0.1361111111111111, 0.1643835616438356],
        "numbers": [0.007407407407407408, 0.8080821917808219, 0.125, 0.1643835616438356],
        "smiley": [0.14351851851851852, 0.8080821917808219, 0.10277777777777777, 0.1643835616438356],
        "spacebar": [0.25555555555555554, 0.8080821917808219, 0.48703703703703705, 0.1643835616438356],
        ".": [0.7546296296296297, 0.8080821917808219, 0.1, 0.1643835616438356],
        "enter": [0.8648148148148148, 0.8080821917808219, 0.12962962962962962, 0.1643835616438356],
    },
    "uppercase": {
        "Q": [0.007407407407407408, 0.19356164383561643, 0.08796296296296297, 0.1643835616438356],
        "W": [0.10462962962962963, 0.19356164383561643, 0.08796296296296297, 0.1643835616438356],
        "E": [0.20462962962962963, 0.19356164383561643, 0.08796296296296297, 0.1643835616438356],
        "R": [0.30462962962962964, 0.19356164383561643, 0.08796296296296297, 0.1643835616438356],
        "T": [0.4046296296296296, 0.19356164383561643, 0.08796296296296297, 0.1643835616438356],
        "Y": [0.5046296296296297, 0.19356164383561643, 0.08796296296296297, 0.1643835616438356],
        "U": [0.6046296296296296, 0.19356164383561643, 0.08796296296296297, 0.1643835616438356],
        "I": [0.7046296296296296, 0.19356164383561643, 0.08796296296296297, 0.1643835616438356],
        "O": [0.8046296296296296, 0.19356164383561643, 0.08796296296296297, 0.1643835616438356],
        "P": [0.9046296296296297, 0.19356164383561643, 0.08796296296296297, 0.1643835616438356],
        "A": [0.05740740740740741, 0.40082191780821917, 0.08796296296296297, 0.1643835616438356],
        "S": [0.15555555555555556, 0.40082191780821917, 0.08796296296296297, 0.1643835616438356],
        "D": [0.25555555555555554, 0.40082191780821917, 0.08796296296296297, 0.1643835616438356],
        "F": [0.35462962962962963, 0.40082191780821917, 0.08796296296296297, 0.1643835616438356],
        "G": [0.4546296296296296, 0.40082191780821917, 0.08796296296296297, 0.1643835616438356],
        "H": [0.5546296296296296, 0.40082191780821917, 0.08796296296296297, 0.1643835616438356],
        "J": [0.6546296296296297, 0.40082191780821917, 0.08796296296296297, 0.1643835616438356],
        "K": [0.7546296296296297, 0.40082191780821917, 0.08796296296296297, 0.1643835616438356],
        "L": [0.8555555555555555, 0.40082191780821917, 0.08796296296296297, 0.1643835616438356],
        "shift": [0.007407407407407408, 0.5994520547945206, 0.1361111111111111, 0.1643835616438356],
        "Z": [0.15555555555555556, 0.5994520547945206, 0.08796296296296297, 0.1643835616438356],
        "X": [0.25555555555555554, 0.5994520547945206, 0.08796296296296297, 0.1643835616438356],
        "C": [0.35462962962962963, 0.5994520547945206, 0.08796296296296297, 0.1643835616438356],
        "V": [0.4546296296296296, 0.5994520547945206, 0.08796296296296297, 0.1643835616438356],
        "B": [0.5546296296296296, 0.5994520547945206, 0.08796296296296297, 0.1643835616438356],
        "N": [0.6546296296296297, 0.5994520547945206, 0.08796296296296297, 0.1643835616438356],
        "M": [0.7546296296296297, 0.5994520547945206, 0.08796296296296297, 0.1643835616438356],
        "backspace": [0.8555555555555555, 0.5994520547945206, 0.1361111111111111, 0.1643835616438356],
        "numbers": [0.007407407407407408, 0.8080821917808219, 0.125, 0.1643835616438356],
        "smiley": [0.14351851851851852, 0.8080821917808219, 0.10277777777777777, 0.1643835616438356],
        "spacebar": [0.25555555555555554, 0.8080821917808219, 0.48703703703703705, 0.1643835616438356],
        ".": [0.7546296296296297, 0.8080821917808219, 0.1, 0.1643835616438356],
        "enter": [0.8648148148148148, 0.8080821917808219, 0.12962962962962962, 0.1643835616438356],
    },
    "numbers": {
        "1": [0.007407407407407408, 0.19356164383561643, 0.08796296296296297, 0.1643835616438356],
        "2": [0.10462962962962963, 0.19356164383561643, 0.08796296296296297, 0.1643835616438356],
        "3": [0.20462962962962963, 0.19356164383561643, 0.08796296296296297, 0.1643835616438356],
        "4": [0.30462962962962964, 0.19356164383561643, 0.08796296296296297, 0.1643835616438356],
        "5": [0.4046296296296296, 0.19356164383561643, 0.08796296296296297, 0.1643835616438356],
        "6": [0.5046296296296297, 0.19356164383561643, 0.08796296296296297, 0.1643835616438356],
        "7": [0.6046296296296296, 0.19356164383561643, 0.08796296296296297, 0.1643835616438356],
        "8": [0.7046296296296296, 0.19356164383561643, 0.08796296296296297, 0.1643835616438356],
        "9": [0.8046296296296296, 0.19356164383561643, 0.08796296296296297, 0.1643835616438356],
        "0": [0.9046296296296297, 0.19356164383561643, 0.08796296296296297, 0.1643835616438356],
        "-": [0.007407407407407408, 0.40082191780821917, 0.08796296296296297, 0.1643835616438356],
        "/": [0.10462962962962963, 0.40082191780821917, 0.08796296296296297, 0.1643835616438356],
        ":": [0.20462962962962963, 0.40082191780821917, 0.08796296296296297, 0.1643835616438356],
        ";": [0.30462962962962964, 0.40082191780821917, 0.08796296296296297, 0.1643835616438356],
        "(": [0.4046296296296296, 0.40082191780821917, 0.08796296296296297, 0.1643835616438356],
        ")": [0.5046296296296297, 0.40082191780821917, 0.08796296296296297, 0.1643835616438356],
        "$": [0.6046296296296296, 0.40082191780821917, 0.08796296296296297, 0.1643835616438356],
        "&": [0.7046296296296296, 0.40082191780821917, 0.08796296296296297, 0.1643835616438356],
        "@": [0.8046296296296296, 0.40082191780821917, 0.08796296296296297, 0.1643835616438356],
        '"': [0.9046296296296297, 0.40082191780821917, 0.08796296296296297, 0.1643835616438356],
        "shift": [0.007407407407407408, 0.5994520547945206, 0.1361111111111111, 0.1643835616438356],
        ",": [0.3101851851851852, 0.5994520547945206, 0.12, 0.1643835616438356],
        "?": [0.44044444444444445, 0.5994520547945206, 0.12, 0.1643835616438356],
        "!": [0.5707037037037037, 0.5994520547945206, 0.12, 0.1643835616438356],
        "'": [0.70596296296296297, 0.5994520547945206, 0.12, 0.1643835616438356],
        "backspace": [0.8551851851851852, 0.5994520547945206, 0.1361111111111111, 0.1643835616438356],
        "letters": [0.007407407407407408, 0.8080821917808219, 0.125, 0.1643835616438356],
        "smiley": [0.14351851851851852, 0.8080821917808219, 0.10277777777777777, 0.1643835616438356],
        "spacebar": [0.25555555555555554, 0.8080821917808219, 0.48703703703703705, 0.1643835616438356],
        ".": [0.7546296296296297, 0.8080821917808219, 0.1, 0.1643835616438356],
        "enter": [0.8648148148148148, 0.8080821917808219, 0.12962962962962962, 0.1643835616438356],
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

    def __init__(  # noqa: C901
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
            capabilities["wdaLocalPort"] = 8000 + (device if device is not None else 0)
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

        # Set the keyboard as default
        if self.platform == ANDROID:
            self.select_keyboard(keyboard)

        # Get the right layout
        if self.keyboard == GBOARD:
            self.detected = GboardLayoutDetector(self.driver, self._tap)
            self.layout = self.detected.layout
        elif self.keyboard == TAPPA:
            self.detected = TappaLayoutDetector(self.driver, self._tap)
            self.layout = self.detected.layout
        elif self.keyboard == FLEKSY:
            self.detected = FleksyLayoutDetector(self.driver)
            self.layout = self.detected.layout
        elif self.keyboard == IOS:
            self.detected = IosLayoutDetector(self.driver, self._tap)
            self.layout = self.detected.layout
        elif self.keyboard == KBKITPRO:
            self.detected = KbkitproLayoutDetector(self.driver, self._tap)
            self.layout = self.detected.layout
        elif self.keyboard == KBKITOSS:
            self.detected = KbkitossLayoutDetector(self.driver, self._tap)
            self.layout = self.detected.layout
        elif self.keyboard == SWIFTKEY:
            self.detected = SwiftkeyLayoutDetector(self.driver, self._tap)
            self.layout = self.detected.layout
        elif self.keyboard == YANDEX:
            self.detected = YandexLayoutDetector(self.driver, self._tap)
            self.layout = self.detected.layout
        else:
            raise ValueError(
                f"Unknown keyboard : {self.keyboard}. Please specify `{GBOARD}`, `{TAPPA}`, `{FLEKSY}`, "
                f"`{SWIFTKEY}`, `{YANDEX}`, `{KBKITPRO}`, `{KBKITOSS}` or `{IOS}`."
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

    def select_keyboard(self, keyboard):
        """Searches the IME of the desired keyboard and selects it, only for Android.

        Args:
            keyboard (str): Keyboard to search.
        """
        if keyboard not in KEYBOARD_PACKAGE:
            print(
                f"Warning ! {keyboard}'s IME isn't provided (in `KEYBOARD_PACKAGE`), can't automatically select the "
                "keyboard."
            )
            return

        ime_list = subprocess.check_output(["adb", "shell", "ime", "list", "-s"], universal_newlines=True)
        ime_name = None
        for ime in ime_list.strip().split("\n"):
            if KEYBOARD_PACKAGE[keyboard] in ime:
                ime_name = ime
                break
        if ime_name:
            subprocess.run(
                ["adb", "shell", "settings", "put", "secure", "show_ime_with_hard_keyboard", "1"],
                stdout=subprocess.PIPE,
            )
            subprocess.run(["adb", "shell", "ime", "enable", ime_name], stdout=subprocess.PIPE)
            subprocess.run(["adb", "shell", "ime", "set", ime_name], stdout=subprocess.PIPE)

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
            if self.platform == IOS:
                self.typing_field.clear()
            if self.keyboard == KBKITPRO or self.keyboard == KBKITOSS or self.keyboard == FLEKSY:
                # In the case of KeyboardKit / Fleksy, after pasting the content, typing a space
                # trigger a punctuation (because previous context may end with a space)
                # To avoid this behavior, break the cycle by typing a backspace
                self._tap(self.layout["lowercase"]["backspace"])
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
                    if self.keyboard == SWIFTKEY:
                        # Swiftkey needs double tap, otherwise we are capslocking
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

                if c != "'" or self.keyboard in [GBOARD, SWIFTKEY]:
                    # For some reason, when `'` is typed, the keyboard automatically goes back
                    # to lowercase, so no need to re-tap the button (unless the keyboard is GBoard / Swiftkey).
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
            xpath_root=f"./*/*[@package='{KEYBOARD_PACKAGE[GBOARD]}']",
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


class KbkitproLayoutDetector(LayoutDetector):
    """Layout detector for the KeyboardKit Pro demo keyboard. See
    `LayoutDetector` for more information.
    """

    def __init__(self, *args, **kwargs):
        super().__init__(
            *args,
            xpath_root=".//XCUIElementTypeOther[XCUIElementTypeButton and XCUIElementTypeTextField]",
            xpath_keys=".//XCUIElementTypeButton",
            android=False,
            **kwargs,
        )

    def get_suggestions(self) -> List[str]:
        """Method to retrieve the keyboard suggestions from the XML tree.

        Returns:
            List of suggestions from the keyboard.
        """
        suggestions = []

        for data in self.driver.page_source.split("<XCUIElementTypeOther"):
            if "<XCUIElementTypeTextField" in data:
                pred_part = data.split("<XCUIElementTypeTextField")[0]
                if "<XCUIElementTypeButton" in pred_part and 'name="Add"' in pred_part:
                    for elem in pred_part.split(">")[2:]:
                        if "<XCUIElementTypeTextField" in elem:
                            break
                        m = re.search(r"name=\"([^\"]*)\"", elem)
                        if m:
                            name = m.group(1)
                            suggestions.append(name.replace("“", "").replace("”", ""))

        return suggestions


class KbkitossLayoutDetector(LayoutDetector):
    """Layout detector for the KeyboardKit OSS demo keyboard. See
    `LayoutDetector` for more information.
    """

    def __init__(self, *args, **kwargs):
        super().__init__(
            *args,
            xpath_root=".//XCUIElementTypeOther[XCUIElementTypeButton and XCUIElementTypeStaticText]",
            xpath_keys=".//XCUIElementTypeButton",
            android=False,
            **kwargs,
        )

    def get_suggestions(self) -> List[str]:
        """Method to retrieve the keyboard suggestions from the XML tree.

        Returns:
            List of suggestions from the keyboard.
        """
        suggestions = []

        for data in self.driver.page_source.split("<XCUIElementTypeOther"):
            if ", Subtitle" in data:
                pred_part = data.split(", Subtitle")[0]
                for elem in pred_part.split(">")[1:]:
                    m = re.search(r"name=\"([^\"]*)\"?", elem)
                    if m:
                        name = m.group(1)
                        suggestions.append(name.replace("“", "").replace("”", ""))

        return suggestions


class SwiftkeyLayoutDetector(LayoutDetector):
    """Layout detector for the Swiftkey keyboard. See `LayoutDetector` for more
    information.
    """

    def __init__(self, *args, **kwargs):
        super().__init__(
            *args,
            xpath_root=f"./*/*[@package='{KEYBOARD_PACKAGE[SWIFTKEY]}']",
            xpath_keys=".//*[@class='android.view.View'][@content-desc]",
            **kwargs,
        )

    def get_suggestions(self) -> List[str]:
        """Method to retrieve the keyboard suggestions from the XML tree.

        Returns:
            List of suggestions from the keyboard.
        """
        suggestions = []

        # Get the raw content as text, weed out useless elements
        for data in self.driver.page_source.split("<android.widget.FrameLayout"):
            if "com.touchtype.swiftkey" in data and "<android.view.View " in data:
                sections = data.split("<android.view.View ")
                for section in sections[1:]:
                    m = re.search(r"content-desc=\"([^\"]*)\"", section)
                    if m:
                        suggestions.append(html.unescape(m.group(1)))
                break

        return suggestions


class YandexLayoutDetector(LayoutDetector):
    """Layout detector for the Yandex keyboard. See `LayoutDetector` for more
    information.
    """

    def __init__(self, *args, **kwargs):
        super().__init__(
            *args,
            xpath_root=f"./*/*[@package='{KEYBOARD_PACKAGE[YANDEX]}']",
            xpath_keys=".//*[@class='ya.d'][@content-desc]",
            **kwargs,
        )

    def get_suggestions(self) -> List[str]:
        """Method to retrieve the keyboard suggestions from the XML tree.

        Returns:
            List of suggestions from the keyboard.
        """
        suggestions = []

        # Get the raw content as text, weed out useless elements
        section = self.driver.page_source.split("<javaClass")

        for line in section.split("\n"):
            if f"{KEYBOARD_PACKAGE[YANDEX]}" in line:
                m = re.search(r"content-desc=\"([^\"]*)\"", section)
                if m:
                    suggestions.append(html.unescape(m.group(1)))

        return suggestions


class TappaLayoutDetector(LayoutDetector):
    """Layout detector for the Tappa keyboard. See `LayoutDetector` for more
    information.
    """

    def __init__(self, *args, **kwargs):
        super().__init__(
            *args,
            xpath_root=f"./*/*[@package='{KEYBOARD_PACKAGE[TAPPA]}']",
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
        section = self.driver.page_source.split(f"{KEYBOARD_PACKAGE[TAPPA]}:id/toolbar")[1].split(
            "</android.widget.FrameLayout>"
        )[0]

        for line in section.split("\n"):
            if "<android.widget.TextView" in line:
                m = re.search(r"text=\"([^\"]*)\"", line)
                if m:
                    suggestions.append(html.unescape(m.group(1)))

        return suggestions


class FleksyLayoutDetector(LayoutDetector):
    """Layout detector for the Fleksy keyboard. See `LayoutDetector` for more
    information.

    Note that this class is only semi-automatically detected : the layout
    itself is not detected, but the suggestions are retrieved from the XML tree
    (no need to rely on OCR, much faster). The layout is hard-coded for now.
    """

    def __init__(self, driver: webdriver.Remote):
        self.driver = driver

        # Adapt the layout to the screen
        w = FLEKSY_LAYOUT["keyboard_frame"][2]
        h = FLEKSY_LAYOUT["keyboard_frame"][3]
        self.layout = {"keyboard_frame": FLEKSY_LAYOUT["keyboard_frame"]}
        for layout_name in ["lowercase", "uppercase", "numbers"]:
            for key_name, key_frame in FLEKSY_LAYOUT[layout_name].items():
                if layout_name not in self.layout:
                    self.layout[layout_name] = {}
                self.layout[layout_name][key_name] = [
                    int(key_frame[0] * w),
                    int(key_frame[1] * h),
                    int(key_frame[2] * w),
                    int(key_frame[3] * h),
                ]

    def get_suggestions(self) -> List[str]:
        """Method to retrieve the keyboard suggestions from the XML tree.

        Returns:
            List of suggestions from the keyboard.
        """
        suggestions = []

        # Get the raw content as text, weed out useless elements
        sections = [
            s
            for s in self.driver.page_source.split("XCUIElementTypeOther")
            if "XCUIElementTypeStaticText" in s and "XCUIElementTypeButton" not in s
        ]

        for s in sections:
            m = re.search(r"name=\"([^\"]*)\"", s)
            if m:
                suggestions.append(html.unescape(m.group(1)))

        return suggestions
