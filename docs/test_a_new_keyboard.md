# Test a new keyboard

To be able to test a keyboard not supported yet by Kebbie you will need to do some steps before run the tests.

## Device setup

* Setup Appium (check [emulator setup](/emu_setup.md))
* Setup the emulator (check [emulator setup](/emu_setup.md#))

## Installing the keyboard on the device
* Install the desired keyboard on the device
* Go to the ```"Languages and input methods"``` section in the device's settings
* Access to the ```"On screen keyboards"``` section
* Enable the keyboard and select it as the default keyboard

## Get full elements tree:

* Prepare the code to open any app with a text input using Appium.
    For example using these capabilities to open Firefox 
    app:
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
* Press the input field to open the keyboard in any application
* Run the method ```driver.getPageSource()``` on your code
* Get the XML returned by that method and then filter it by the keyboard package (e.g. ```"com.newkeyboardCompany.newkeyboard"```)
* Find the keyboard frame coordinates, the layout size and the data of each key by checking the content-desc or the resource-id
* Get the root element of the keyboard and then the type for each key


## Add a new keyboard to Kebbie:
* Add the name of the new keyboard in the available choices in the file ```kebbie > kebbie > cmd.py``` (e.g. 
  ```choices = ["gboard", "ios", "kbkitpro", "kbkitoss", "tappa", "fleksy", "newKeyboard"]```)
* If it’s an Android keyboard add it to the ```instantiate_correctors``` list in the ```cmd.py``` file
Add in the file ```kebbie > kebbie > emulator.py``` the name of the new keyboard (e.g. ```NEWKEYBOARD = "newkeyboard"```)
* If there is any content in the keyboard that we want to ignore from the mapping, add it in the ```CONTENT_TO_IGNORE``` list at the ```emulator.py``` file (e.g. ```"Gallery"```)
* If there is any content in the keyboard that we want to map with another name, add it in the ```CONTENT_TO_RENAME``` list at the ```emulator.py``` file (e.g. ```"Find": "enter"```)
* Create a layout detector class with the keyboard name (e.g. ```class NewKeyboardLayoutDetector(LayoutDetector)```)
  adding the methods to get the root, the keys and the suggestions (see the ```GboardLayoutDetector``` class for an example)
* Finally, in the ```__init__``` method at the ```emulator.py``` file, add the name of the keyboard in the ```Get the 
right layout``` section using the layout detector class and add the keyboard to the error handling like:
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
* First check the key mapping running the command ```kebbie show_layout -K newkkeyboard```
* If the keys mapping fails trying to get the numbers layout, add a ```print(self.driver.page_source)``` before the 
method ```self.tap(layout["lowercase"]["numbers"]``` and launch the command again to get the key to switch to numbers adding it in the ```CONTENT_TO_RENAME``` list (e.g. ```"Digit keyboard": "numbers"```)
* Then evaluate the keyboard with the command ```kebbie evaluate -K newkeyboard```