# Usage

`kebbie` exposes a class [Corrector][kebbie.Corrector] and a function [evaluate()][kebbie.evaluate].

The user creates a custom class which inherits from [Corrector][kebbie.Corrector], over-write methods such as [auto_correct()][kebbie.Corrector.auto_correct], [auto_complete()][kebbie.Corrector.auto_complete], [predict_next_word()][kebbie.Corrector.predict_next_word], and [resolve_swipe()][kebbie.Corrector.resolve_swipe].  
Then the user calls [evaluate()][kebbie.evaluate] with the custom [Corrector][kebbie.Corrector], which will run the benchmark and return the results as a `Dictionary` (it contains various metrics for each task).

---

Let's see how to do that in details with a basic example : we will use [`pyspellchecker`](https://github.com/barrust/pyspellchecker), a pure-Python spell-checking library, and test it using `kebbie` to see how well it performs.

## Creating your own [Corrector][kebbie.Corrector]

First, we define a subclass of [Corrector][kebbie.Corrector], and we implement the constructor.

In our case, the constructor will simply initialize the `pyspellchecker` library :

```python
from spellchecker import SpellChecker
from kebbie import Corrector


class ExampleCorrector(Corrector):
    def __init__(self):
        self.spellchecker = SpellChecker()
```

---

For this example we are only interested in auto-correction (spell-checking). So we need to over-write the [auto_correct()][kebbie.Corrector.auto_correct] method.

The implementation is straightforward thanks to `pyspellchecker` :

```python hl_lines="11-13"
from typing import List

from spellchecker import SpellChecker
from kebbie import Corrector


class ExampleCorrector(Corrector):
    def __init__(self):
        self.spellchecker = SpellChecker()

    def auto_correct(self, context: str, keystrokes, word: str) -> List[str]:
        cands = self.spellchecker.candidates(word)
        return list(cands) if cands is not None else []
```

---

Great ! We have a testable [Corrector][kebbie.Corrector] class.

!!! info
    We didn't overwrite the methods for the other tasks, and that's fine !  
    Other tasks' score will be set to 0, but we are just interested in auto-correction score anyway.

## Calling the [evaluate()][kebbie.evaluate] function

Once we have the [Corrector][kebbie.Corrector] implemented, we can simply instantiate it and call the [evaluate()][kebbie.evaluate] function :

```python hl_lines="4 17-18"
from typing import List

from spellchecker import SpellChecker
from kebbie import Corrector, evaluate


class ExampleCorrector(Corrector):
    def __init__(self):
        self.spellchecker = SpellChecker()

    def auto_correct(self, context: str, keystrokes, word: str) -> List[str]:
        cands = self.spellchecker.candidates(word)
        return list(cands) if cands is not None else []


if __name__ == "__main__":
    corrector = ExampleCorrector()
    results = evaluate(corrector)

    # Save the results in a local file for later inspection
    with open("results.json", "w") as f:
        json.dump(results, f, ensure_ascii=False, indent=4)
```

And that's it !

---

Now you can just run your script. It might take some time to go over the 2 000 sentences of the test set, but eventually it will end and you should see a file `results.json` in your working directory.

## Inspecting the results

Go ahead and open the file `results.json`.

It contains the results of the test, with various metrics.

Let's go over the content quickly.

First, the metrics are divided into each tasks :
* `next_word_prediction`
* `auto_completion`
* `auto_correction`
* `swipe_resolution`

!!! info
    At the end of the file, there is also a field `overall_score`. This is just an aggregation of the scores of all tasks, to have an easy way to compare runs.

As expected, if you look at other tasks than `auto_correction`, their score is zero. That's expected, because we are interested only on auto-correction, and we didn't implement the code for the other tasks.

Let's take a deeper look at the `auto_correction` results.

---

First, we have
