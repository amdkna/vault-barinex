## Detailed Stepwise Roadmap to Full Standards Compliance

Below is an expanded, granular breakdown for each of the seven phases—with explicit file actions, content templates, and validation checks.

---

### Phase 1: Repo Bootstrapping & Tooling

**Goal:** Establish versioning, formatting, linting, and pre‑commit/CI scaffolds.

<!-- #### 1.1 Initialize Version Control

* Create `.gitignore` with entries for:

  * Python: `__pycache__/`, `*.py[cod]`, `.env`
  * IDEs: `.vscode/`, `.idea/`
  * OS: `.DS_Store`, `Thumbs.db`
* Commit an initial empty repo state. -->
<!-- 
#### 1.2 Editor Configuration

* Write `.editorconfig`:

  * `root = true`
  * Set `indent_style = space`, `indent_size = 4`, `charset = utf-8`, `trim_trailing_whitespace = true`, `insert_final_newline = true`. -->

<!-- #### 1.3 Pre-Commit Hooks

* Create `.pre-commit-config.yaml` with hooks:

  * `repos:`

    * `- repo: https://github.com/psf/black`, `rev: stable`, `hooks: - id: black`
    * `- repo: https://github.com/PyCQA/isort`, `rev: 5.x`, `hooks: - id: isort`
    * `- repo: https://gitlab.com/pycqa/flake8`, `rev: 3.x`, `hooks: - id: flake8`
    * `- repo: https://github.com/pre-commit/mirrors-mypy`, `rev: v0.971`, `hooks: - id: mypy` -->

<!-- #### 1.4 pyproject.toml Setup

* Under `[build-system]`:

  * `requires = ["setuptools>=42","wheel"]`
  * `build-backend = "setuptools.build_meta"
    `
* Add tool configs:

  * `[tool.black]`: `line-length = 88`, `target-version = ['py38']`
  * `[tool.isort]`: `profile = "black"`
  * `[tool.flake8]`: `max-line-length = 88`, `extend-ignore = E203`
  * `[tool.mypy]`: `python_version = 3.8`, `strict = true` -->

<!-- #### 1.5 Dependency Files

* `requirements.txt`: pin runtime libs, e.g.:

  * `pydantic==1.10.2`
  * `requests==2.31.0`
* `requirements-dev.txt`: add:

  * `pytest==7.4.0`, `pytest-cov==4.1.0`, `flake8`, `mypy`, `pre-commit`

#### 1.6 Initial CI Workflow -->

<!-- * Create `.github/workflows/ci.yml`:

  * **Jobs**:

    * **lint**: runs pre-commit (black, isort, flake8, mypy)
    * **test**: installs dev+prod deps, runs `pytest --cov=src` with coverage report
  * **Matrix**:

    * Python versions: \[3.8, 3.9, 3.10]
  * **Caching**:

    * Cache pip (`~/.cache/pip`), pre-commit -->

<!-- #### 1.7 Badges & Version Placeholder

* In `README.md` header:

  * Add markdown badges for GitHub Actions, PyPI (once published), coverage.
* In `pyproject.toml`:

  * Add `version = "0.1.0"`, `name = "barinex"`, `description = "…"`, `authors = ["Your Name <email>"]`.

**Validation:** All hooks pass locally; `pre-commit run --all-files` returns clean.

--- -->

### Phase 2: Documentation & Guides

**Goal:** Consolidate all policy docs, create templates, and craft operational guides.

#### 2.1 Create `docs/` Directory

* Copy the six protocol files into `docs/`:

  * Use kebab-case filenames (e.g. `document-writing-protocol.md`).
* Add `docs/architecture.md`:

  * Include diagrams (ASCII or Mermaid) of modules and data flow.
* Add `docs/contribution.md`:

  * Define branching strategy (e.g., GitFlow), PR template, code review checklist.

#### 2.2 Top-Level README

* `README.md` sections:

  1. **Project Title & Description**
  2. **Badges**
  3. **Table of Contents**
  4. **Installation**

     * `pip install -e .`
     * Environment variables setup
  5. **Quickstart**

     * CLI examples
     * Configuration file sample
  6. **Usage**

     * Code import examples
  7. **Testing**

     * How to run `pytest`
  8. **Contributing**

     * Link to `docs/contribution.md`

#### 2.3 CHANGELOG & LICENSE

* `CHANGELOG.md`:

  * Initialize with `## [0.1.0] - YYYY-MM-DD` and `### Added` placeholders.
* `LICENSE.md`: paste MIT text, include copyright line.

**Validation:** Render docs locally; check links and headings hierarchy.

---

### Phase 3: Codebase Restructure & Renaming

**Goal:** Flatten legacy scripts into the new package layout and standardize naming.

#### 3.1 Create Package Skeleton

* Under `src/` directory:

  * `mkdir -p src/barinex/{config,db,fetcher,services,indicators,utils}`
  * Touch `__init__.py` in each directory.

#### 3.2 Move & Rename Files

| Original                    | New Location                                             |
| --------------------------- | -------------------------------------------------------- |
| `first_data_finder.py`      | `scripts/find_first_data.py`                             |
| `evaluate_indicators_at.py` | Merge into `src/barinex/services/indicator_evaluator.py` |
| `indicator_evaluator.py`    | Archive or remove if duplicate                           |
| `ohlcv_handler.py`          | `src/barinex/services/ohlcv_handler.py`                  |
| `ohlcv_data_fetcher.py`     | `src/barinex/fetcher/ohlcv_data_fetcher.py`              |

#### 3.3 Update Imports

* Run `isort --profile=black -rc src/`.
* Globally search `from first_data_finder` → `from barinex.scripts.find_first_data`.
* Use relative imports within package.

#### 3.4 Scaffold Root Modules

* Create `src/barinex/`:

  * `cli.py`: blank click group with stub commands.
  * `logger.py`, `exceptions.py`, `constants.py`: empty files with module docstring.
  * `config/settings.py`: placeholder for Pydantic settings.

**Validation:** After moves, `pytest` and `flake8` report no missing imports.

---

### Phase 4: Configuration, Logging & Errors

**Goal:** Implement robust application-level infrastructure.

#### 4.1 Config Loader Implementation

* In `src/barinex/config/settings.py`:

  ```python
  from pydantic import BaseSettings

  class Settings(BaseSettings):
      api_key: str
      db_url: str
      symbol_list: list[str]
      # load yaml
      class Config:
          env_file = ".env"
          env_file_encoding = "utf-8"
  ```
* Add `indicator_settings.yml` and `symbols.yml` examples under `config/`.
* Write unit tests to assert defaults and overrides.

#### 4.2 Logging Setup

* In `logger.py`:

  ```python
  import logging
  from logging.handlers import RotatingFileHandler

  def setup_logging(level: str, log_file: str):
      fmt = "%(asctime)s %(levelname)s %(name)s: %(message)s"
      datefmt = "%Y-%m-%dT%H:%M:%S%z"
      handler = RotatingFileHandler(log_file, maxBytes=10**7, backupCount=3)
      logging.basicConfig(level=level, format=fmt, datefmt=datefmt, handlers=[handler])
  ```
* Allow tests to inject `StreamHandler`.

#### 4.3 Exceptions Hierarchy

* In `exceptions.py`:

  ```python
  class AppError(Exception):
      def __init__(self, message: str, code: int = 1):
          super().__init__(message)
          self.code = code

  class FetchError(AppError): pass
  class ParseError(AppError): pass
  class ValidationError(AppError): pass
  class DatabaseError(AppError): pass
  ```
* Refactor modules to catch low-level errors and wrap in these classes.
* Update docstrings to include `:raises:` sections.

**Validation:** Create tests that deliberately raise and catch each exception.

---

### Phase 5: Core Logic & Utilities Enhancement

**Goal:** Refactor business logic for clarity, add type hints, and centralize shared code.

#### 5.1 Services Refactoring

* In `services/ohlcv_handler.py`:

  * Split `load_ohlcv` and `transform_ohlcv` functions.
  * Add type signatures: `def load_ohlcv(symbol: str) -> pd.DataFrame:`.
  * Docstrings with `Args`, `Returns`, `Raises`.
* In `services/indicator_evaluator.py`:

  * Expose `evaluate_indicators(df: pd.DataFrame) -> dict[str, float]`.
  * Validate input shape and column presence.

#### 5.2 Utilities Extraction

* Create `utils/resample.py`:

  ```python
  def resample_df(df: DataFrame, rule: str, agg: dict[str, str]) -> DataFrame:
      """Resample OHLCV data according to `rule` with specified aggregates."""
      return df.resample(rule).agg(agg)
  ```
* Add `utils/converters.py` if date parsing or timezone conversion logic exists.
* In `utils/__init__.py`, define `__all__ = ["resample_df"]`.

#### 5.3 Indicators Modularization

* For each indicator (e.g. `indicators/adx.py`):

  ```python
  def compute_adx(df: DataFrame, period: int = 14) -> Series:
      """Compute the Average Directional Index."""
      # implementation
  ```
* Write unit tests mapping known input to expected output in `tests/unit/test_indicators.py`.

**Validation:** Run `mypy src/barinex` and ensure no type errors; `pytest` passes.

---

### Phase 6: Package & Distribution Setup

**Goal:** Make the project installable and ready for PyPI.

#### 6.1 Complete Packaging Metadata

* In `pyproject.toml` under `[project]`:

  * `readme = "README.md"`, `license = { file = "LICENSE.md" }`, `keywords = [...]`, `classifiers = [...]`.
* Ensure `include = ["src/barinex"]` in `[tool.setuptools.packages.find]`.

#### 6.2 Define Console Entry Points

* In `src/barinex/cli.py`, use `click.group()` and add commands:

  ```python
  @click.group()
  def cli():
      """barinex CLI"""
  @cli.command()
  def backfill():
      """Fetch and store historical data"""
  ```
* In `pyproject.toml`:

  ```toml
  [project.scripts]
  barinex = "barinex.cli:cli"
  ```

#### 6.3 Installation Tests

* Execute:

  * `pip install -e .`
  * `which barinex` returns path
  * `barinex --help` shows commands.

**Validation:** No import errors when installed; CLI commands return exit code 0.

---

### Phase 7: Testing, Coverage & CI Finalization

**Goal:** Solidify the test suite, enforce high coverage, and finalize CI pipeline.

#### 7.1 Structure & Fixtures

* `tests/conftest.py`:

  * Fixture for `settings` loading from temp files
  * HTTP mocking via `responses` or `pytest_httpserver`
  * SQLite in-memory DB setup/teardown

#### 7.2 Expand Test Coverage

* **Unit Tests**:

  * `tests/unit/test_utils.py`
  * `tests/unit/test_indicators.py`
  * `tests/unit/test_resample.py`
* **Integration Tests**:

  * `tests/integration/test_fetcher.py` (mock remote API)
  * `tests/integration/test_db_operations.py`
* **E2E Tests**:

  * `tests/e2e/test_cli_workflow.py` (invoke `barinex backfill`, verify DB)

#### 7.3 Coverage & Quality Gates

* Update `pytest.ini`:

  ```ini
  [pytest]
  addopts = --cov=src --cov-report=xml --cov-fail-under=90
  ```
* In CI (`ci.yml`):

  * Add `coverage.xml` artifact
  * Fail build if coverage < 90%

#### 7.4 Lint & Type Checks

* CI `lint` job:

  * `pre-commit run --all-files`
  * `mypy src/barinex --strict`
* Document any `# type: ignore` exceptions in `docs/`

#### 7.5 Finalize Badges & Release Prep

* Update `README.md` with final badge URLs:

  * Coverage (Coveralls/Codecov)
  * PyPI
* Tag v0.1.0 in Git and draft GitHub Release notes from `CHANGELOG.md`.

**Validation:** All CI jobs pass; draft PyPI package successfully builds with `twine check dist/*`.

---

*This plan ensures every file is named and structured per standards, code quality tools are in place, docs are complete, and CI enforces all gates. Ready to kick off Phase 1?*
