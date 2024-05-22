# Leaderboard

[//]: # (A bit of explanation is required for this page)
[//]: # (There is a Mkdocs hook (defined in `docs/hooks.py`) that will read the content of this page, extract the path of result files listed here, read their content, and organize their score into a table)

| Keyboard | Score | Next-word prediction | Auto-completion | Auto-correction |
|---------:|:-----:|:--------------------:|:---------------:|:---------------:|
>>>Fleksy|results/fleksy.json
>>>iOS keyboard|results/ios.json
>>>KeyboardKit Open-source|results/keyboardkit_oss.json
>>>KeyboardKit Pro|results/keyboardkit_pro.json
>>>Gboard|results/gboard.json
>>>Swiftkey|results/swiftkey.json

!!! info
    The metrics used in this leaderboard are :

    * For next-word prediction : top-3 accuracy
    * For auto-completion : top-3 accuracy
    * For auto-correction : F-score

    See [Understanding the metrics](how_testing_is_done.md#understanding-the-metrics) for more details.

    The overall score is a _weighted sum_ of each task's score.
