# Emulator setup

## Installing Appium 2.0

Appium is required to communicate between Python and the emulators.

Install Appium 2.0 by following [their official documentation](https://appium.io/docs/en/latest/quickstart/install/).

---

Then install the required drivers :

```bash
# For Android
appium driver install uiautomator2

# For iOS
appium driver install xcuitest
```

---

To start Appium, open a new terminal and type :

```bash
appium
```

!!! info "Note"
    Once it's running, don't close the terminal.  
    Appium needs to run in order for Python to communicate with the emulators.

## Setting up Android emulator

### Creating the emulator

* Install [Android Studio](https://developer.android.com/studio)
* Create a new virtual device
![](assets/emu_setup_1.png)
* Select the phone (`Pixel 2` for example) and the system image (`Tiramisu - Android 13.0` for example)

### Starting the emulator

Once you have created the emulator, you should be able to see its name from the command line :

```bash
emulator -list-avds
```

??? failure "If you encounter `command not found: emulator`"
    If the command fails with `command not found: emulator`, you need to update your path accordingly :

    ```bash
    export ANDROID_HOME=/Users/<username>/Library/Android/sdk
    export PATH=$ANDROID_HOME/platform-tools:$ANDROID_HOME/emulator:$PATH
    ```

You can start the emulator directly from the command line with :  
*(so you don't need to run Android Studio, which takes a lot of resources)*

```bash
emulator -avd <name> -no-snapshot-load
```

Once started, make sure you can see it. From another terminal, run :

```bash
adb devices
```

??? failure "If you encounter `command not found: adb`"
    If the command fails with `command not found: adb`, you need to update your path accordingly :

    ```bash
    export ANDROID_HOME=/Users/<username>/Library/Android/sdk
    export PATH=$ANDROID_HOME/platform-tools:$ANDROID_HOME/emulator:$PATH
    ```

!!! info
    In Android, to open the keyboard, we access a notepad website ([www.justnotepad.com](www.justnotepad.com)).

    The reason we do that is because it's the easiest way to access a typing field, and it works across versions and emulators.

### Preparing GBoard

GBoard is enabled by default on Android, so there is nothing to do.

!!! tip
    You can make sure GBoard is indeed the selected keyboard by going to the `Settings` -> `System` -> `Languages & Input` -> `On-screen keyboard`.

---

By default, GBoard has the clipboard enabled, and it may interfere with the layout detection. You can disable the clipboard in the settings of GBoard :

![](assets/emu_setup_5.png){ width="300" align=left }

![](assets/emu_setup_6.png){ width="300" }

Make sure to disable the clipboard :

![](assets/emu_setup_7.png){ width="300" }

## Setting up iOS emulator

### Creating the emulator

* Install [XCode](https://apps.apple.com/us/app/xcode/id497799835?mt=12)
* Open WebDriverAgent in Xcode :
```bash
open ~/.appium/node_modules/appium-xcuitest-driver/node_modules/appium-webdriveragent/WebDriverAgent.xcodeproj
```
* Go to `Signing & Capabilities` of the project :

![](assets/ios_setup_1.png)

* Then click `Team` and select your Apple ID
* You should do this for the three following targets : `WebDriverAgentLib`, `WebDriverAgentRunner`, `IntegrationApp`.

---

Now, make sure you can properly build the `WebDriverAgentRunner` target : select it in the top bar and run it (button "play") :

![](assets/ios_setup_2.png)

If all the stars are aligned, it should start the emulator !

### Starting the emulator

Once you have ensured the emulator runs properly, you should be able to start it from the command line (without Xcode open).

First, check the list of emulators available :

```bash
xcrun simctl list
```

Example of emulators listed :

```
-- iOS 17.4 --
    iPhone SE (3rd generation) (96ADAD77-ECE6-420E-B56C-505E0C16231B) (Shutdown)
    iPhone 15 (128F95FC-F499-4B09-A3B2-55937BF52B0B) (Shutdown)
    iPhone 15 Plus (86591FC6-B3E7-43A2-9E9B-D4A2A90DAF31) (Shutdown)
    iPhone 15 Pro (9D38F87D-273B-4D8F-8AD5-E901C1974C1E) (Shutdown)
    iPhone 15 Pro Max (15EF57B4-69E6-4369-9534-70692A2023E5) (Shutdown)
    iPad Air (5th generation) (252D522B-CEAA-4085-BE17-A453BC219755) (Shutdown)
    iPad (10th generation) (39F2ADD2-2FCF-44C3-9DC9-4CC4D50875E9) (Shutdown)
    iPad mini (6th generation) (59125B84-4ED1-40C1-8457-3CE824394385) (Shutdown)
    iPad Pro (11-inch) (4th generation) (DB122D71-F358-48DA-B11C-D25305657E7F) (Shutdown)
    iPad Pro (12.9-inch) (6th generation) (1100927A-B631-4678-AB19-02EA4F680537) (Shutdown)
```

Then you can start the device you want with :

```bash
xcrun simctl boot <UUID>
```

For example, to start `iPhone 15 Pro`, you should run :

```bash
xcrun simctl boot 9D38F87D-273B-4D8F-8AD5-E901C1974C1E
```

!!! warning
    The `xcrun simctl boot` command only launch the simulator background service, to launch the foreground GUI, run :

    ```bash
    open -a Simulator
    ```

!!! note
    To shutdown the simulator, run :

    ```bash
    xcrun simctl shutdown <UUID>
    ```

### Preparing iOS Keyboard

iOS Keyboard is the default keyboard on iOS, so there is nothing to do to enable it.

However, predictions and auto-corrections are disabled by default. They should be enabled :

* Go to `Settings` :

![](assets/ios_setup_4.png){ width="250" }

* Then go to `General` :

![](assets/ios_setup_5.png){ width="250" }

* Then go to `Keyboard` :

![](assets/ios_setup_6.png){ width="250" }

* Then enable `Auto-Correction` and `Predictive Text` :

![](assets/ios_setup_7.png){ width="250" }

## Parallel Android emulators

In order to run tests faster, we can setup multiple Android emulators, and run the [evaluate()][kebbie.evaluate] function in parallel.

First, follow the section above to [setup one Android emulator](#setting-up-android-emulator).

Once it's done, you can simply clone it from Android Studio :

![](assets/emu_setup_2.png)

Clone it several times. Once the emulators are created, you should be able to list them from the command line :

```bash
emulator -list-avds
```

Then open several terminal, and in each terminal open one emulator :

```bash
emulator -avd <name> -no-snapshot-load
```

After they started, you should be able to see them with :

```bash
adb devices
```

!!! tip
    Once you can see the emulators with the `adb devices` command, there is nothing else to do ! You can run the `kebbie` CLI just like you would do for a single emulator : the CLI will detect the running emulators with the `adb devices` command.
