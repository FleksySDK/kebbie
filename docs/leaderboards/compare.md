---
hide:
  - toc
---

# Leaderboard

[//]: # (A bit of explanation is required for this page)
[//]: # (There is a Mkdocs hook (defined in `docs/hooks.py`) that will read the content of this page. Any line starting with `>>>` will be extracted and replaced with the scores found in the corresponding result file.)
[//]: # (The format to follow is : `>>>{name}|{result_file_name}|{optional_additional_fields}`)

| Keyboard | Overall score | Typo detection rate | Auto-correction relevance | Auto-completion success rate | Next-word prediction success rate | SDK available |
|---------:|:-------------:|:-------------------:|:--------------------------------:|:---------------:|:-------------------:|:-------------:|
>>>Fleksy|results/fleksy.json|:fontawesome-solid-circle-check:{ .v_icon }
>>>iOS keyboard|results/ios.json|:fontawesome-regular-circle-xmark:{ .x_icon }
>>>KeyboardKit Open-source|results/keyboardkit_oss.json|:fontawesome-solid-circle-check:{ .v_icon }
>>>KeyboardKit Pro|results/keyboardkit_pro.json|:fontawesome-solid-circle-check:{ .v_icon }
>>>Gboard|results/gboard.json|:fontawesome-regular-circle-xmark:{ .x_icon }
>>>Swiftkey|results/swiftkey.json|:fontawesome-regular-circle-xmark:{ .x_icon }
>>>Tappa|results/tappa.json|:fontawesome-solid-circle-check:{ .v_icon }
>>>Yandex|results/yandex.json|:fontawesome-regular-circle-xmark:{ .x_icon }

### Metrics

=== "Overall score"

    A single, general score representing the performances of the keyboard across all tasks.

    :material-trending-up: _Higher is better._

=== "Typo detection rate"

    Percentage of typos detected and corrected by the keyboard.

    :material-trending-up: _Higher is better._

=== "Auto-correction relevance"

    Percentage of auto-corrections that are relevant (the auto-corrected word indeed contain a typo).  
    The correction is irrelevant when a word is correctly typed, but the keyboard corrects it to something else.

    :material-trending-up: _Higher is better._

=== "Auto-completion success rate"

    Percentage of words correctly auto-completed.

    :material-trending-up: _Higher is better._

=== "Next-word prediction success rate"

    Percentage of words correctly predicted from the context.

    :material-trending-up: _Higher is better._
