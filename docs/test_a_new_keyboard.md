# Test a new keyboard

To be able to test a keyboard not supported yet by Kebbie you will need to do some steps before run the tests.


## Device setup
To get the elements of the keyboard to be able to map the keys and then evaluate the keyboard you need 
to have Appium 2 correctly installed and the emulator ready. 

So you need to:


* Setup Appium (check [emulator setup](emu_setup.md))
* Setup the emulator (check [emulator setup](emu_setup.md#))


## Installing the keyboard on the device
First of all install the desired keyboard on the device by dragging the apk to the emulator or installing the app 
from the store.

Once it's installed, if it hasn't any setup wizard, go to the `Languages and input methods` section in the 
device's settings.

Then access to the `On screen keyboards` section.

And finally enable and select the keyboard.


## Get full elements tree:

Prepare the code to open any app with a text input field using Appium. For example using these capabilities to open Firefox app:
```bash
{
"platformName": "Android",
"deviceName": "test",
"automationName": "UiAutomator2",
"appPackage": "org.mozilla.firefox",
"appActivity": "org.mozilla.fenix.HomeActivity",
"browserName": ""
}
```

Press the input field to open the keyboard in any application

Run the method `driver.getPageSource()` on your code

Get the XML returned by that method and then filter it by the keyboard package (e.g. `com.newkeyboardCompany.newkeyboard`)

Find the keyboard frame coordinates, the layout size and the data of each key by checking the content-desc or the resource-id

Get the root element of the keyboard and then the type for each key


## Add a new keyboard to Kebbie:
Add the name of the new keyboard in the available choices in the file `kebbie > kebbie > cmd.py`

Example:

```bash
choices = ["gboard", "ios", "kbkitpro", "kbkitoss", "tappa", "fleksy", "newKeyboard"]
```

And in the file `kebbie > kebbie > emulator.py`

Example:

```bash
NEWKEYBOARD = "newkeyboard"
```

!!! info "Note"
    If it’s an Android keyboard add it to the `instantiate_correctors` list in the `cmd.py` file

!!! info "Note"
    If there is any content in the keyboard that we want to ignore from the mapping, add it in the `CONTENT_TO_IGNORE` list at the `emulator.py` file (e.g. `"Gallery"`)

!!! info "Note"
    If there is any content in the keyboard that we want to map with another name, add it in the `CONTENT_TO_RENAME` list at the `emulator.py` file (e.g. `"Find": "enter"`)

Create a layout detector class with the keyboard name adding the methods to get the root, the keys and the suggestions (see the `GboardLayoutDetector` class for an example)

Example copying and editing the Gboard layout detector:

```bash
class NewKeyboardLayoutDetector(LayoutDetector):
    """Layout detector for the NewKeyboard keyboard. See `LayoutDetector` for more
    information.
    """

    def __init__(self, *args, **kwargs):
        super().__init__(
            *args,
            xpath_root=f"./*/*[@package='{KEYBOARD_PACKAGE[NEWKEYBOARD]}']",
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
            if KEYBOARD_PACKAGE[NEWKEYBOARD] in data
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
```

Finally, in the `__init__` method at the `emulator.py` file, add the name of the keyboard in the `Get the 
right layout` section using the layout detector class and add the keyboard to the error handling.

Example:

```bash
elif self.keyboard == NEWKEYBOARD:
    self.detected = NewKeyboardLayoutDetector(self.driver, self._tap)
    self.layout = self.detected.layout
else:
    raise ValueError(
        f"Unknown keyboard : {self.keyboard}. Please specify {GBOARD}, {TAPPA}, {FLEKSY}, "
        f"{NEWKEYBOARD}, {KBKITPRO}, {KBKITOSS} or {IOS}."
    )
```


## Test the new keyboard with Kebbie:
First check the key mapping running the command `kebbie show_layout -K newkkeyboard`

!!! tip
    If the keys mapping fails trying to get the numbers layout, add a `print(self.driver.page_source)` before the method `self.tap(layout["lowercase"]["numbers"]` and launch the command again to get the key to switch to numbers adding it in the `CONTENT_TO_RENAME` list (e.g. `"Digit keyboard": "numbers"`)

Finally evaluate the keyboard with the command `kebbie evaluate -K newkeyboard` and wait until the evaluation 
is finished to get the results.