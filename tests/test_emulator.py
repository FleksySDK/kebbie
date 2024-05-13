import subprocess
from dataclasses import dataclass

import pytest

import kebbie
from kebbie.emulator import Emulator


class DummyStdout:
    def __init__(self, out: str):
        self.out = out

    def decode(self) -> str:
        return self.out


@dataclass
class SubprocessResult:
    stdout: DummyStdout


def test_get_android_devices(monkeypatch):
    def android_subprocess(*args, **kwargs):
        return SubprocessResult(
            DummyStdout("""List of devices attached
emulator-5554	device
emulator-5558	device

""")
        )

    monkeypatch.setattr(subprocess, "run", android_subprocess)

    devices = Emulator.get_android_devices()

    assert len(devices) == 2
    assert devices[0] == "emulator-5554"
    assert devices[1] == "emulator-5558"


def test_get_ios_devices(monkeypatch):
    def ios_subprocess(*args, **kwargs):
        return SubprocessResult(
            DummyStdout("""== Devices ==
-- iOS 14.4 --
    iPhone 12 mini (8A192CB8-A72C-4BBA-9A98-2476E66ABEF8) (Shutdown) (unavailable)
    iPhone 12 (C0E1F6AB-FDA5-4953-BB22-7CDB09D3B303) (Shutdown) (unavailable)
    iPhone 12 Pro (2279B364-4B56-44CA-BC73-DB7B454C9B44) (Shutdown) (unavailable)
    iPhone 12 Pro Max (932FE34B-6B02-44BE-9BA0-04ED5B625212) (Shutdown) (unavailable)
-- iOS 17.2 --
    iPhone 15 (8B06FF67-549A-4CF6-A185-5C574061DF34) (Shutdown)
    iPhone 15 Plus (419EEC34-6540-4CF8-9C22-3322309E4317) (Shutdown)
    iPhone 15 Pro (AD890C91-AFFA-4C90-A459-F004FD68F384) (Shutdown)
    iPhone 15 Pro Max (9ABCC3B6-72C9-43B3-BE18-CC047385F468) (Shutdown)
-- iOS 17.4 --
    iPhone 15 (128F95FC-F499-4B09-A3B2-55937BF52B0B) (Shutdown)
    iPhone 15 Plus (86591FC6-B3E7-43A2-9E9B-D4A2A90DAF31) (Shutdown)
    iPhone 15 Pro (9D38F87D-273B-4D8F-8AD5-E901C1974C1E) (Shutdown)
    iPhone_15_2 (C423F3BC-BC3A-4FFC-B264-C6075B60115F) (Booted)
    iPhone_15_3 (2BEB33D0-8F33-4987-95FC-FD9B7C2BD54D) (Booted)
    iPhone_15_4 (EE0719E9-FF3C-4539-9BCD-9F091B469F93) (Shutdown)
-- Unavailable: com.apple.CoreSimulator.SimRuntime.iOS-16-2 --
    iPhone SE (3rd generation) (8062F6CF-F6C5-4550-A54B-09B203B9E5BC) (Shutdown) (unavailable)
    iPhone 14 (D1BF5412-E294-483D-93AB-8C626AD4C32C) (Shutdown) (unavailable)
    iPhone 14 Plus (28470FD5-F941-4D89-AB50-FA5B6F4D7205) (Shutdown) (unavailable)
    iPhone 14 Pro (3B9978F8-C028-4B8D-8356-35B65971D82D) (Shutdown) (unavailable)
    iPhone 14 Pro Max (9F58CBB4-F9B3-4C0C-BAA1-CCA021AF8ED6) (Shutdown) (unavailable)
    iPad Air (5th generation) (12F98471-71EF-469A-AA56-B308D966D4AE) (Shutdown) (unavailable)
    iPad (10th generation) (6DA8E495-E6FD-425E-9D08-B52A607AC41B) (Shutdown) (unavailable)
    iPad mini (6th generation) (EC7F8EF2-D5A6-437B-9531-E2DBE924FB5A) (Shutdown) (unavailable)
    iPad Pro (11-inch) (4th generation) (49F56D2F-5722-41CD-9C11-D4979084DA3E) (Shutdown) (unavailable)
    iPad Pro (12.9-inch) (6th generation) (08E5485D-D293-4B7B-9831-F29D55EDA053) (Shutdown) (unavailable)
""")
        )

    monkeypatch.setattr(subprocess, "run", ios_subprocess)

    devices = Emulator.get_ios_devices()

    assert len(devices) == 2
    assert devices[0][0] == "17.4"
    assert devices[0][1] == "iPhone_15_2"
    assert devices[1][0] == "17.4"
    assert devices[1][1] == "iPhone_15_3"


def test_undefined_platform():
    with pytest.raises(ValueError) as e:
        Emulator("alien_tech", "gboard")

    assert "Unknown platform" in str(e.value)


class DummyDriver:
    def __init__(self, *args, **kwargs):
        pass

    def implicitly_wait(self, *args, **kwargs):
        pass

    def get_window_size(self):
        return None


@pytest.fixture
def mock_appium_driver(monkeypatch):
    monkeypatch.setattr(kebbie.emulator.webdriver, "Remote", DummyDriver)

    # Also overwrite the `_access_typing_field` method, to avoid accessing anything
    def dont_access_anything(*args, **kwargs):
        pass

    monkeypatch.setattr(Emulator, "_access_typing_field", dont_access_anything)


def test_undefined_keyboard(mock_appium_driver):
    with pytest.raises(ValueError) as e:
        Emulator("android", "alien_keyboard")

    assert "Unknown keyboard" in str(e.value)
