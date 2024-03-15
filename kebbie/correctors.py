"""Module containing the base Corrector class."""
from typing import List, Optional, Tuple

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
            List[str]: The list of correction candidates.
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

        Returns:  # noqa: DAR202
            List[str]: The list of completion candidates.
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
            List[str]: The list of swiped word candidates.
        """
        return []

    def predict_next_word(self, context: str) -> List[str]:
        """Method used for next-word prediction task. Given a context, this
        method should return a list of possible candidates for next-word.

        Args:
            context (str): String representing the previously typed characters
                (the beginning of the sentence basically).

        Returns:
            List[str]: The list of next-word candidates.
        """
        return []

    def profiled_auto_correct(self, *args, **kwargs) -> Tuple[List[str], int, int]:
        """Profiled (memory & runtime) version of `auto_correct` method.

        No need to overwrite this method, unless you want to specify a custom
        memory and/or runtime measure.

        Returns:
            Tuple[List[str], int, int]: The first value is the return value of
                the profiled method (list of candidates). Second value is the
                memory consumption in bytes, and the third value is runtime in
                nano seconds.
        """
        return profile_fn(self.auto_correct, *args, **kwargs)

    def profiled_auto_complete(self, *args, **kwargs) -> Tuple[List[str], int, int]:
        """Profiled (memory & runtime) version of `auto_complete` method.

        No need to overwrite this method, unless you want to specify a custom
        memory and/or runtime measure.

        Returns:
            Tuple[List[str], int, int]: The first value is the return value of
                the profiled method (list of candidates). Second value is the
                memory consumption in bytes, and the third value is runtime in
                nano seconds.
        """
        return profile_fn(self.auto_complete, *args, **kwargs)

    def profiled_resolve_swipe(self, *args, **kwargs) -> Tuple[List[str], int, int]:
        """Profiled (memory & runtime) version of `resolve_swipe` method.

        No need to overwrite this method, unless you want to specify a custom
        memory and/or runtime measure.

        Returns:
            Tuple[List[str], int, int]: The first value is the return value of
                the profiled method (list of candidates). Second value is the
                memory consumption in bytes, and the third value is runtime in
                nano seconds.
        """
        return profile_fn(self.resolve_swipe, *args, **kwargs)

    def profiled_predict_next_word(self, *args, **kwargs) -> Tuple[List[str], int, int]:
        """Profiled (memory & runtime) version of `predict_next_word` method.

        No need to overwrite this method, unless you want to specify a custom
        memory and/or runtime measure.

        Returns:
            Tuple[List[str], int, int]: The first value is the return value of
                the profiled method (list of candidates). Second value is the
                memory consumption in bytes, and the third value is runtime in
                nano seconds.
        """
        return profile_fn(self.predict_next_word, *args, **kwargs)
