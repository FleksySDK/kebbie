# Usage

`kebbie` exposes a class `Corrector` and a function `evaluate()`.

The user creates a custom class which inherits from  `Corrector`, over-write methods such as `auto_correct()`, `auto_complete()`, `predict_next_word()`, and `resolve_swipe()`.  
Then the user calls `evaluate()` with the custom `Corrector`, which will run the benchmark and return the results as a `Dictionary` (it contains various metrics for each task).

Let's see how to do that in details with a basic example : we will use [`pyspellchecker`](https://github.com/barrust/pyspellchecker) a pure-Python spell-checking library, to test how well it performs.

## Creating your own `Corrector`

A `Corrector` instance represents the NLP capabilities of a keyboard.
