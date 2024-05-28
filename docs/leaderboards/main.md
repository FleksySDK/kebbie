# Leaderboard

[//]: # (A bit of explanation is required for this page)
[//]: # (There is a Mkdocs hook (defined in `docs/hooks.py`) that will read the content of this page. Any line starting with `>>>` will be extracted and replaced with the scores found in the corresponding result file.)
[//]: # (The format to follow is : `>>>{name}|{result_file_name}|{optional_additional_fields}`)

| Keyboard | Score | Auto-correction | Auto-completion | Next-word prediction |
|---------:|:-----:|:---------------:|:---------------:|:--------------------:|
>>>Fleksy|results/fleksy.json
>>>iOS keyboard|results/ios.json
>>>KeyboardKit Open-source|results/keyboardkit_oss.json
>>>KeyboardKit Pro|results/keyboardkit_pro.json
>>>Gboard|results/gboard.json
>>>Swiftkey|results/swiftkey.json
>>>Tappa|results/tappa.json
>>>Yandex|results/yandex.json

!!! info
    The metrics used in this leaderboard are :

    * For next-word prediction : top-3 accuracy
    * For auto-completion : top-3 accuracy
    * For auto-correction : F-score

    See [Understanding the metrics](../how_testing_is_done.md#understanding-the-metrics) for more details.

    The overall score is a _weighted sum_ of each task's score.
