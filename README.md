<h1 align="center">kebbie</h1>
<p align="center">
Python Template repository
</p>

<p align="center">
    <a href="https://github.com/FleksySDK/kebbie/releases"><img src="https://img.shields.io/github/release/FleksySDK/kebbie.svg" alt="GitHub release" /></a>
    <a href="https://github.com/FleksySDK/kebbie/actions/workflows/pytest.yaml"><img src="https://github.com/FleksySDK/kebbie/actions/workflows/pytest.yaml/badge.svg" alt="Test status" /></a>
    <a href="https://github.com/FleksySDK/kebbie/actions/workflows/lint.yaml"><img src="https://github.com/FleksySDK/kebbie/actions/workflows/lint.yaml/badge.svg" alt="Lint status" /></a>
    <img src=".github/badges/coverage.svg" alt="Coverage status" />
    <a href="https://FleksySDK.github.io/kebbie"><img src="https://img.shields.io/website?down_message=failing&label=docs&up_color=green&up_message=passing&url=https%3A%2F%2FFleksySDK.github.io%2Fkebbie" alt="Docs" /></a>
    <a href="https://github.com/FleksySDK/kebbie/blob/main/LICENSE"><img src="https://img.shields.io/badge/License-MIT-yellow.svg" alt="licence" /></a>
</p>

<p align="center">
  <a href="#description">Description</a> •
  <a href="#install">Install</a> •
  <a href="#usage">Usage</a> •
  <a href="#contribute">Contribute</a>
  <br>
  <a href="https://FleksySDK.github.io/kebbie/" target="_blank">Documentation</a>
</p>


<h2 align="center">Description</h2>

TODO


<h2 align="center">Install</h2>

Install `kebbie` by running :


```
pip install kebbie
```

---

For development, you can install it locally by first cloning the repository :

```
git clone https://github.com/FleksySDK/kebbie.git
cd kebbie
pip install -e .
```

<h2 align="center">Usage</h2>

TODO


<h2 align="center">Contribute</h2>

To contribute, install the package locally, create your own branch, add your code (and tests, and documentation), and open a PR !

### Pre-commit hooks

Pre-commit hooks are set to check the code added whenever you commit something.

If you never ran the hooks before, install it with :

```bash
pre-commit install
```

---

Then you can just try to commit your code. If your code does not meet the quality required by linters, it will not be committed. You can just fix your code and try to commit again !

---

You can manually run the pre-commit hooks with :

```bash
pre-commit run --all-files
```

### Tests

When you contribute, you need to make sure all the unit-tests pass. You should also add tests if necessary !

You can run the tests with :

```bash
pytest
```

---

Tests are not included in the pre-commit hooks, because running the tests might be slow, and for the sake of developpers we want the pre-commit hooks to be fast !

Pre-commit hooks will not run the tests, but it will automatically update the coverage badge !

### Documentation

The documentation should be kept up-to-date. You can visualize the documentation locally by running :

```bash
mkdocs serve
```
