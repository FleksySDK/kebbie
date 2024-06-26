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
import json
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

??? abstract "Results for `pyspellchecker==0.8.1` at the time of writing"
    ```json
    {
        "next_word_prediction": {
            "score": {
                "accuracy": 0,
                "top3_accuracy": 0,
                "n": 46978
            },
            "per_domain": {
                "narrative": {
                    "accuracy": 0,
                    "top3_accuracy": 0,
                    "n": 32044
                },
                "dialogue": {
                    "accuracy": 0,
                    "top3_accuracy": 0,
                    "n": 14934
                }
            },
            "performances": {
                "mean_memory": "865.0 KB",
                "min_memory": "8.24 KB",
                "max_memory": "1.1 MB",
                "mean_runtime": "5.91 μs",
                "fastest_runtime": "0 ns",
                "slowest_runtime": "2.13 ms"
            }
        },
        "auto_completion": {
            "score": {
                "accuracy": 0,
                "top3_accuracy": 0,
                "n": 46910
            },
            "per_domain": {
                "narrative": {
                    "accuracy": 0,
                    "top3_accuracy": 0,
                    "n": 32002
                },
                "dialogue": {
                    "accuracy": 0,
                    "top3_accuracy": 0,
                    "n": 14908
                }
            },
            "per_completion_rate": {
                "<25%": {
                    "accuracy": 0,
                    "top3_accuracy": 0,
                    "n": 1335
                },
                "25%~50%": {
                    "accuracy": 0,
                    "top3_accuracy": 0,
                    "n": 8891
                },
                "50%~75%": {
                    "accuracy": 0,
                    "top3_accuracy": 0,
                    "n": 25757
                },
                ">75%": {
                    "accuracy": 0,
                    "top3_accuracy": 0,
                    "n": 10927
                }
            },
            "per_other": {
                "without_typo": {
                    "accuracy": 0,
                    "top3_accuracy": 0,
                    "n": 43450
                },
                "with_typo": {
                    "accuracy": 0,
                    "top3_accuracy": 0,
                    "n": 3460
                }
            },
            "performances": {
                "mean_memory": "865.0 KB",
                "min_memory": "424 B",
                "max_memory": "1.1 MB",
                "mean_runtime": "9.57 μs",
                "fastest_runtime": "0 ns",
                "slowest_runtime": "89.8 ms"
            }
        },
        "auto_correction": {
            "score": {
                "accuracy": 0.87,
                "precision": 0.47,
                "recall": 0.35,
                "fscore": 0.41,
                "top3_accuracy": 0.88,
                "top3_precision": 0.56,
                "top3_recall": 0.5,
                "top3_fscore": 0.53,
                "n_typo": 6302,
                "n": 48864
            },
            "per_domain": {
                "narrative": {
                    "accuracy": 0.87,
                    "precision": 0.48,
                    "recall": 0.36,
                    "fscore": 0.42,
                    "top3_accuracy": 0.89,
                    "top3_precision": 0.57,
                    "top3_recall": 0.51,
                    "top3_fscore": 0.54,
                    "n_typo": 4247,
                    "n": 32948
                },
                "dialogue": {
                    "accuracy": 0.86,
                    "precision": 0.44,
                    "recall": 0.34,
                    "fscore": 0.39,
                    "top3_accuracy": 0.88,
                    "top3_precision": 0.53,
                    "top3_recall": 0.48,
                    "top3_fscore": 0.51,
                    "n_typo": 2055,
                    "n": 15916
                }
            },
            "per_typo_type": {
                "DELETE_SPELLING_SYMBOL": {
                    "accuracy": 0.83,
                    "precision": 0.15,
                    "recall": 0.07,
                    "fscore": 0.099,
                    "top3_accuracy": 0.84,
                    "top3_precision": 0.26,
                    "top3_recall": 0.14,
                    "top3_fscore": 0.19,
                    "n_typo": 129,
                    "n": 1000
                },
                "DELETE_SPACE": {
                    "accuracy": 0.83,
                    "precision": 0.11,
                    "recall": 0.051,
                    "fscore": 0.074,
                    "top3_accuracy": 0.83,
                    "top3_precision": 0.11,
                    "top3_recall": 0.051,
                    "top3_fscore": 0.074,
                    "n_typo": 137,
                    "n": 1062
                },
                "DELETE_PUNCTUATION": {
                    "accuracy": 0,
                    "precision": 0,
                    "recall": 0,
                    "fscore": 0,
                    "top3_accuracy": 0,
                    "top3_precision": 0,
                    "top3_recall": 0,
                    "top3_fscore": 0,
                    "n_typo": 0,
                    "n": 0
                },
                "DELETE_CHAR": {
                    "accuracy": 0.86,
                    "precision": 0.42,
                    "recall": 0.29,
                    "fscore": 0.35,
                    "top3_accuracy": 0.88,
                    "top3_precision": 0.55,
                    "top3_recall": 0.48,
                    "top3_fscore": 0.52,
                    "n_typo": 559,
                    "n": 4334
                },
                "ADD_SPELLING_SYMBOL": {
                    "accuracy": 0,
                    "precision": 0,
                    "recall": 0,
                    "fscore": 0,
                    "top3_accuracy": 0,
                    "top3_precision": 0,
                    "top3_recall": 0,
                    "top3_fscore": 0,
                    "n_typo": 0,
                    "n": 0
                },
                "ADD_SPACE": {
                    "accuracy": 0,
                    "precision": 0,
                    "recall": 0,
                    "fscore": 0,
                    "top3_accuracy": 0,
                    "top3_precision": 0,
                    "top3_recall": 0,
                    "top3_fscore": 0,
                    "n_typo": 0,
                    "n": 0
                },
                "ADD_PUNCTUATION": {
                    "accuracy": 0,
                    "precision": 0,
                    "recall": 0,
                    "fscore": 0,
                    "top3_accuracy": 0,
                    "top3_precision": 0,
                    "top3_recall": 0,
                    "top3_fscore": 0,
                    "n_typo": 0,
                    "n": 0
                },
                "ADD_CHAR": {
                    "accuracy": 0.9,
                    "precision": 0.6,
                    "recall": 0.59,
                    "fscore": 0.59,
                    "top3_accuracy": 0.92,
                    "top3_precision": 0.66,
                    "top3_recall": 0.76,
                    "top3_fscore": 0.7,
                    "n_typo": 855,
                    "n": 6629
                },
                "SUBSTITUTE_CHAR": {
                    "accuracy": 0.86,
                    "precision": 0.47,
                    "recall": 0.35,
                    "fscore": 0.4,
                    "top3_accuracy": 0.88,
                    "top3_precision": 0.55,
                    "top3_recall": 0.49,
                    "top3_fscore": 0.53,
                    "n_typo": 863,
                    "n": 6691
                },
                "SIMPLIFY_ACCENT": {
                    "accuracy": 0,
                    "precision": 0,
                    "recall": 0,
                    "fscore": 0,
                    "top3_accuracy": 0,
                    "top3_precision": 0,
                    "top3_recall": 0,
                    "top3_fscore": 0,
                    "n_typo": 0,
                    "n": 0
                },
                "SIMPLIFY_CASE": {
                    "accuracy": 0.82,
                    "precision": 0,
                    "recall": 0,
                    "fscore": 0,
                    "top3_accuracy": 0.82,
                    "top3_precision": 0,
                    "top3_recall": 0,
                    "top3_fscore": 0,
                    "n_typo": 403,
                    "n": 3125
                },
                "TRANSPOSE_CHAR": {
                    "accuracy": 0.89,
                    "precision": 0.58,
                    "recall": 0.54,
                    "fscore": 0.56,
                    "top3_accuracy": 0.91,
                    "top3_precision": 0.64,
                    "top3_recall": 0.7,
                    "top3_fscore": 0.66,
                    "n_typo": 1313,
                    "n": 10181
                },
                "COMMON_TYPO": {
                    "accuracy": 0.85,
                    "precision": 0.39,
                    "recall": 0.26,
                    "fscore": 0.32,
                    "top3_accuracy": 0.88,
                    "top3_precision": 0.53,
                    "top3_recall": 0.45,
                    "top3_fscore": 0.49,
                    "n_typo": 1725,
                    "n": 13375
                }
            },
            "per_number_of_typos": {
                "1": {
                    "accuracy": 0.87,
                    "precision": 0.47,
                    "recall": 0.36,
                    "fscore": 0.41,
                    "top3_accuracy": 0.89,
                    "top3_precision": 0.56,
                    "top3_recall": 0.51,
                    "top3_fscore": 0.54,
                    "n_typo": 5984,
                    "n": 46397
                },
                "2": {
                    "accuracy": 0.86,
                    "precision": 0.43,
                    "recall": 0.29,
                    "fscore": 0.35,
                    "top3_accuracy": 0.87,
                    "top3_precision": 0.47,
                    "top3_recall": 0.36,
                    "top3_fscore": 0.41,
                    "n_typo": 292,
                    "n": 2264
                },
                "3+": {
                    "accuracy": 0.83,
                    "precision": 0.17,
                    "recall": 0.077,
                    "fscore": 0.11,
                    "top3_accuracy": 0.84,
                    "top3_precision": 0.23,
                    "top3_recall": 0.12,
                    "top3_fscore": 0.16,
                    "n_typo": 26,
                    "n": 202
                }
            },
            "performances": {
                "mean_memory": "866.0 KB",
                "min_memory": "7.05 KB",
                "max_memory": "1.1 MB",
                "mean_runtime": "358.0 ms",
                "fastest_runtime": "69.1 μs",
                "slowest_runtime": "77.1 s"
            }
        },
        "swipe_resolution": {
            "score": {
                "accuracy": 0,
                "top3_accuracy": 0,
                "n": 417
            },
            "per_domain": {
                "narrative": {
                    "accuracy": 0,
                    "top3_accuracy": 0,
                    "n": 313
                },
                "dialogue": {
                    "accuracy": 0,
                    "top3_accuracy": 0,
                    "n": 104
                }
            },
            "performances": {
                "mean_memory": "860.0 KB",
                "min_memory": "96.0 KB",
                "max_memory": "1.1 MB",
                "mean_runtime": "24.5 μs",
                "fastest_runtime": "0 ns",
                "slowest_runtime": "4.68 ms"
            }
        },
        "overall_score": 0.164
    }
    ```

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

First, we have a `score` field, which contains various overall metrics about the auto-correction capability : precision, recall, F-score, etc...

There is also a value `n`, which shows the total number of words we tried to auto-correct, and `n_typo`, the number of words which contained a typo.

For auto-correction, the metric we care about is the F-score, as it measure both the precision and the recall.

!!! info
    For more information about the metrics and their meaning, check out the [Metrics](how_testing_is_done.md#metrics) page.

---

Then we have a `per_domain` field, which also contains the same metrics, but divided into the various domains of our dataset. We can see that `pyspellchecker` is better at correcting `narrative` data than `dialogue` data, since the F-score is higher.

We then have a `per_typo_type` field, which shows the metrics for each type of typo introduced.  
Note that the [evaluate()][kebbie.evaluate] does not introduce all type of typos by default, so some of them are set to `0`.

After we have a `per_number_of_typos` field, which gives the metrics depending on how many typos were introduced in that word.

And finally we have a field `performances`, which show the memory consumption and runtime for the [auto_correct()][kebbie.Corrector.auto_correct] method that we wrote.

## A note about multiprocessing

Under the hood, [evaluate()][kebbie.evaluate] uses multiprocessing to run faster.

It means that your [Corrector][kebbie.Corrector] should be pickable !

!!! success "Example"
    In the example above, the implementation provided is already pickable, so there is nothing to do.

If you need to make your class pickable, just implement the `__reduce__()` magic method, like this :

```python hl_lines="12 14-16"
from typing import Tuple

from kebbie import Corrector


class GreatCorrector(Corrector):
    def __init__(self, model_path: str):
        self.m_path = model_path

        # Because of this (imaginary) non-pickable attribute,
        # the class `GreatCorrector` is not pickable as-is
        self.non_pickable_model = load_model(model_path)

    def __reduce__(self) -> Tuple:
        # But by implementing `__reduce__()`, we can make it pickable !
        return (GreatCorrector, (self.m_path,))
```


## Advanced usage

### Leveraging the keystroke coordinates

Did you notice that in our [auto_correct()][kebbie.Corrector.auto_correct] implementation, there is an argument `keystrokes` that we didn't use ?

```python hl_lines="5"
class ExampleCorrector(Corrector):
    def __init__(self):
        self.spellchecker = SpellChecker()

    def auto_correct(self, context: str, keystrokes, word: str) -> List[str]:
        cands = self.spellchecker.candidates(word)
        return list(cands) if cands is not None else []
```

This `keystrokes` argument is a list of keystrokes coordinates (one per character of the typed `word`).

These coordinates may hold useful information : for example on a QWERTY keyboard, if the word typed is `lovw` but the keystroke for `w` is very close to the border of the `e` key... There is a great chance that the word should be auto-corrected to `love`...

---

These coordinates are defined in a layout file internally. To interact easily with the layout, you can use the [LayoutHelper][kebbie.layout.LayoutHelper] class.

You can use the method [get_key_info()][kebbie.layout.LayoutHelper.get_key_info] to retrieve data about the key for the given character.

For example, let's compute the distance between the first keystroke of the word, and the key for the character `w` :

```python
import math
from kebbie.layout import LayoutHelper

layout = LayoutHelper()

def auto_correct(self, context: str, keystrokes, word: str) -> List[str]:
    _, _, w_key_center_x, w_key_center_y, _ = layout.get_key_info("w")
    if len(keystrokes) > 0 and keystrokes[0] is not None:
        print(math.dist(keystrokes[0], [w_key_center_x, w_key_center_y]))
```

### Custom dataset

The [evaluate()][kebbie.evaluate] function uses a good default dataset (see [Test data](how_testing_is_done.md#test-data)) to run the evaluation.

However, you might want to run the evaluation on your own dataset.

You can do this by passing your custom dataset to the [evaluate()][kebbie.evaluate] function :

```python hl_lines="1 3"
my_dataset = load_my_private_dataset()
corrector = ExampleCorrector()
results = evaluate(corrector, dataset=my_dataset)
```

Your custom dataset should be a `Dict[str, List[str]]`, where each keys of the dictionary represents a specific domain, and the values are just the list of sentences.

### Get insights on most common mistakes

When trying to improve your models, you might want to take a look at the most common mistakes your model is doing.

You can achieve this simply by passing `track_mistakes=True` to the [evaluate()][kebbie.evaluate] function :

```python hl_lines="2"
corrector = ExampleCorrector()
results = evaluate(corrector, track_mistakes=True)
```

It will record the most common mistakes your [Corrector][kebbie.Corrector] is doing, and add them in a new field (`most_common_mistakes`) in the returned results.

The mistakes are tracked for the following tasks : next-word prediction, auto-completion, and auto-correction.

Let's look at the most common mistakes for our example with `pyspellchecker` :

```json
"auto_correction": [
    [
        "Count",
        "Expected",
        "Predictions",
        "Context"
    ],
    [
        266,
        "I'm",
        "[ism, h'm]",
        "Kolten beckoned Aida over wanting to hear what he had to say Aida I want to know what's on your mind Kolten said I'm"
    ],
    [
        157,
        "to",
        "[tho]",
        "Destanie was so angry that he felt like he might explode He felt the hot blood rushing to his head and his fists clenched tightly at his sides He took a deep breath and tried tho"
    ],
    ...
```

Here we can see that we track several thing for each mistake :

* `Count` : The total number of times this mistake happened
* `Expected` : The expected word
* `Predictions` : The model's predictions
* `Context` : An example of a sentence where the mistake happened

So we can see that the most common mistake of `pyspellchecker` is to try to auto correct `I'm` into `ism`, even though it should not be corrected. This mistake was encountered 266 times during the evaluation.

The second most common mistake is to not auto-correct `tho`, even though it should be corrected to `to`. This mistake was encountered 157 times during the evaluation.

!!! tip
    By default, the 1 000 most common mistakes will be saved. You can specify a different `n`, with the `n_most_common_mistakes` argument :

    ```python hl_lines="2"
    corrector = ExampleCorrector()
    results = evaluate(corrector, track_mistakes=True, n_most_common_mistakes=150)
    ```

### Other arguments

Specify the number of processes to be used for multiprocessing with the `n_proc` argument :

```python hl_lines="2"
corrector = ExampleCorrector()
results = evaluate(corrector, n_proc=4)
```

!!! info "Note"
    If `None` is given, [evaluate()][kebbie.evaluate] will use `os.cpu_count()` (the number of CPU of your machine). Defaults to `None`.

---

Specify a different seed with the `seed` argument :

```python hl_lines="2"
corrector = ExampleCorrector()
results = evaluate(corrector, seed=36)
```

---

Specify a different Beta for the F-score calculation (see the [Metrics](how_testing_is_done.md#auto-correction) section) with the `beta` argument :

```python hl_lines="2"
corrector = ExampleCorrector()
results = evaluate(corrector, beta=1.2)
```
