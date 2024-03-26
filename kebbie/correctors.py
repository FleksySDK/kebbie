"""Module containing the base Corrector class."""

from typing import List, Optional, Tuple

from kebbie.emulator import Emulator
from kebbie.utils import profile_fn


class Corrector:
    """Base class for Corrector, which is the component being tested.

    Child classes should overwrite `auto_correct()`, `auto_complete()`,
    `resolve_swipe()`, and `predict_next_word()`.

    By default, the implementation for these methods is dummy : just return an
    empty list of candidates.
    """

    def auto_correct(
        self,
        context: str,
        keystrokes: List[Optional[Tuple[float, float]]],
        word: str,
    ) -> List[str]:
        """Method used for auto-correction.
        Given a context and a typed word, this method should return a list of
        possible candidates for correction.

        Note that the typed word is given both as a plain string, and as a list
        of keystrokes. The child class overwriting this method can use either
        of them.

        Args:
            context (str): String representing the previously typed characters
                (the beginning of the sentence basically).
            keystrokes (List[Optional[Tuple[float, float]]]): List of positions
                (x and y coordinates) for each keystroke of the word being
                typed.
            word (str): Word being typed (corresponding to the keystrokes).

        Returns:
            The list of correction candidates.
        """
        return []

    def auto_complete(
        self,
        context: str,
        keystrokes: List[Optional[Tuple[float, float]]],
        partial_word: str,
    ) -> List[str]:
        """Method used for auto-completion.
        Given a context and a partially typed word, this method should return
        a list of possible candidates for completion.

        Note that the typed word is given both as a plain string, and as a list
        of keystrokes. The child class overwriting this method can use either
        of them.

        Args:
            context (str): String representing the previously typed characters
                (the beginning of the sentence basically).
            keystrokes (List[Optional[Tuple[float, float]]]): List of positions
                (x and y coordinates) for each keystroke of the word being
                typed.
            partial_word (str): Partial word being typed (corresponding to the
                keystrokes).

        Returns:
            The list of completion candidates.
        """
        return []

    def resolve_swipe(self, context: str, swipe_gesture: List[Tuple[float, float]]) -> List[str]:
        """Method used for resolving a swipe gesture. Given a context and a
        swipe gesture, this method should return a list of possible candidates
        corresponding to this swipe gesture.

        Args:
            context (str): String representing the previously typed characters
                (the beginning of the sentence basically).
            swipe_gesture (List[Tuple[float, float]]): List of positions (x and
                y coordinates) along the keyboard, representing the swipe
                gesture.

        Returns:
            The list of swiped word candidates.
        """
        return []

    def predict_next_word(self, context: str) -> List[str]:
        """Method used for next-word prediction task. Given a context, this
        method should return a list of possible candidates for next-word.

        Args:
            context (str): String representing the previously typed characters
                (the beginning of the sentence basically).

        Returns:
            The list of next-word candidates.
        """
        return []

    def profiled_auto_correct(self, *args, **kwargs) -> Tuple[List[str], int, int]:
        """Profiled (memory & runtime) version of `auto_correct` method.

        No need to overwrite this method, unless you want to specify a custom
        memory and/or runtime measure.

        Returns:
            List of candidates returned from the profiled method.
            Memory consumption in bytes.
            Runtime in nano seconds.
        """
        return profile_fn(self.auto_correct, *args, **kwargs)

    def profiled_auto_complete(self, *args, **kwargs) -> Tuple[List[str], int, int]:
        """Profiled (memory & runtime) version of `auto_complete` method.

        No need to overwrite this method, unless you want to specify a custom
        memory and/or runtime measure.

        Returns:
            List of candidates returned from the profiled method.
            Memory consumption in bytes.
            Runtime in nano seconds.
        """
        return profile_fn(self.auto_complete, *args, **kwargs)

    def profiled_resolve_swipe(self, *args, **kwargs) -> Tuple[List[str], int, int]:
        """Profiled (memory & runtime) version of `resolve_swipe` method.

        No need to overwrite this method, unless you want to specify a custom
        memory and/or runtime measure.

        Returns:
            List of candidates returned from the profiled method.
            Memory consumption in bytes.
            Runtime in nano seconds.
        """
        return profile_fn(self.resolve_swipe, *args, **kwargs)

    def profiled_predict_next_word(self, *args, **kwargs) -> Tuple[List[str], int, int]:
        """Profiled (memory & runtime) version of `predict_next_word` method.

        No need to overwrite this method, unless you want to specify a custom
        memory and/or runtime measure.

        Returns:
            List of candidates returned from the profiled method.
            Memory consumption in bytes.
            Runtime in nano seconds.
        """
        return profile_fn(self.predict_next_word, *args, **kwargs)


class EmulatorCorrector(Corrector):
    """Corrector using an emulated keyboard.

    Args:
        platform (str): Name of the platform used. `android` or `ios`.
        keyboard (str): Name of the keyboard to test.
        device (str): Device UDID to use for the emulator.
        fast_mode (bool): If `True`, only auto-correction will be tested,
            and suggestions will not be retrieved. This is faster because
            we don't take screenshot and run the OCR.
        instantiate_emulator (bool): If `False`, the emulator is not
            initialized (It will only be initialized after being pickled).
            This is useful to quickly create instances of this class,
            without going through the whole layout detection (which takes
            time) 2 times : at initialization and after being pickled.
    """

    def __init__(
        self,
        platform: str,
        keyboard: str,
        device: str = None,
        fast_mode: bool = True,
        ios_name: str = None,
        ios_platform: str = None,
        instantiate_emulator: bool = True,
    ):
        super().__init__()

        self.platform = platform
        self.keyboard = keyboard
        self.device = device
        self.fast_mode = fast_mode
        self.ios_name = ios_name
        self.ios_platform = ios_platform

        self.emulator = None
        if instantiate_emulator:
            self.emulator = Emulator(
                self.platform,
                self.keyboard,
                device=self.device,
                ios_name=self.ios_name,
                ios_platform=self.ios_platform,
            )

        # Typing on keyboard is slow. Because we go through several AC calls
        # in one sentence, keep track of the previously typed context, so we
        # can just type the remaining characters
        self.previous_context = ""

    def __reduce__(self) -> Tuple:
        """This method simply makes the object pickable.

        Returns:
            Tuple of callable and arguments.
        """
        return (
            self.__class__,
            (self.platform, self.keyboard, self.device, self.fast_mode, self.ios_name, self.ios_platform),
        )

    def cached_type(self, context: str, word: str):
        """This class keeps track of the content of the context currently
        typed in the emulator. This method uses this current context to
        determine if we need to retype the sentence or not. Instead of
        always erasing the content being typed, we can directly type the
        remaining characters, which saves up time.

        Args:
            context (str): Context to paste.
            word (str): Word to type.
        """
        sentence = context + word
        if sentence.startswith(self.previous_context):
            # The sentence to type start similarly as the previous context
            # Don't retype everything, just what we need
            self.emulator.type_characters(sentence[len(self.previous_context) :])
        else:
            # The previous context is not right, erase everything and type it
            self.emulator.paste(context)
            self.emulator.type_characters(word)
        self.previous_context = sentence

    def auto_correct(
        self,
        context: str,
        keystrokes: List[Optional[Tuple[float, float]]],
        word: str,
    ) -> List[str]:
        """Implementation of `auto_correct` method for emulated keyboards.

        Args:
            context (str): String representing the previously typed characters
                (the beginning of the sentence basically).
            keystrokes (List[Optional[Tuple[float, float]]]): List of positions
                (x and y coordinates) for each keystroke of the word being
                typed.
            word (str): Word being typed (corresponding to the keystrokes).

        Returns:
            The list of correction candidates.
        """
        self.cached_type(context, word)
        candidates = self.emulator.get_predictions() if not self.fast_mode else []

        candidates = [c for c in candidates if c != ""]

        # On keyboard, the leftmost candidate is the word being typed without
        # any change. If the word doesn't have a typo, this first candidate
        # should be kept as the auto-correction, but if the word has a typo,
        # we should remove it from the candidates list (as it will be
        # auto-corrected).
        # In order to know if it will be auto-corrected or not, we have no
        # choice but type a space and retrieve the current text to see if it
        # was auto-corrected or not.
        self.emulator.type_characters(" ")
        self.previous_context = self.emulator.get_text()
        autocorrection = self.previous_context[len(context) :].strip()

        if len(candidates) == 0:
            candidates = [autocorrection]
        elif candidates[0] != autocorrection:
            candidates.pop(0)
            if autocorrection not in candidates:
                candidates.insert(0, autocorrection)

        return candidates

    def auto_complete(
        self,
        context: str,
        keystrokes: List[Optional[Tuple[float, float]]],
        partial_word: str,
    ) -> List[str]:
        """Implementation of `auto_complete` method for emulated keyboards.

        Args:
            context (str): String representing the previously typed characters
                (the beginning of the sentence basically).
            keystrokes (List[Optional[Tuple[float, float]]]): List of positions
                (x and y coordinates) for each keystroke of the word being
                typed.
            partial_word (str): Partial word being typed (corresponding to the
                keystrokes).

        Returns:
            The list of completion candidates.
        """
        if self.fast_mode:
            return []

        self.cached_type(context, partial_word)
        candidates = self.emulator.get_predictions()

        candidates = [c for c in candidates if c != ""]

        return candidates

    def predict_next_word(self, context: str) -> List[str]:
        """Implementation of `predict_next_word` method for emulated keyboards.

        Args:
            context (str): String representing the previously typed characters
                (the beginning of the sentence basically).

        Returns:
            The list of next-word candidates.
        """
        if self.fast_mode:
            return []

        # In order to get the predictions, the space should be typed
        assert context[-1] == " "
        self.cached_type(context[:-1], " ")
        candidates = self.emulator.get_predictions()
        candidates = [c for c in candidates if c != ""]

        return candidates
