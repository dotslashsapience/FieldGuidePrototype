Contributing to FieldGuidePrototype

This document outlines the standards and workflows we use to maintain high velocity without sacrificing system integrity.

## 1. The Golden Rule: Data is Not Code

Our repository is for logic, not state.

- Never commit `.csv`, `.txt` (scraped data), `.json` (large datasets), or `.env` files.

- All raw and processed data must live in the `/data` directory, which is strictly ignored by Git.

- Large assets should be stored in [S3/Cloud Storage] and referenced via scripts.

## 2. Branching Strategy

We use a simplified feature-branch workflow to keep `main` stable.

- `main`: The source of truth. Always deployable.

- `feature/description-of-change`: For new logic or UI components.

- `fix/issue-name`: For urgent bug fixes.

#### Workflow:

1. Pull latest `main`.

2. Create your branch: `git checkout -b feature/your-feature-name`.

3. Work, commit, and push.

4. Open a Pull Request (PR) for review.

5. Commit and push all to github daily.

## 3. Commit Message Standards

We use the Imperative Mood (e.g., "Add" not "Added"). This matches Git's own internal messaging.

- `feat: ...` (New feature)

- `fix: ...` (Bug fix)

- `docs: ...` (Documentation changes)

- `refactor: ...` (Code change that neither fixes a bug nor adds a feature)

- `chore: ...` (Updating dependencies, build tasks, etc.)

Example: `feat: add exponential backoff to scraper API calls`

## 4. Coding Standards

 ### Style & Formatting

  - Python: Follow PEP 8. Use Black for auto-formatting and Ruff for linting.

  - Indentation: 4 spaces (Python) / 2 spaces (JS). No tabs.

 ### Guidelines:

  - DRY (Don't Repeat Yourself): If you're writing the same logic for the third time, abstract it into a utility function.

  - Error Handling: No silent failures. Use explicit try/except blocks and log errors properly.

  - Modularity: Functions should do one thing and do it well. If a function is >30 lines, it likely needs to be broken down.

  - Naming: Function, Class and variable names should carry enough information that someone unfamiliar with the codebase can read it and understand exactly what it's purpose is.

 ### Environments:
  We use UV for our python environments.

 ### Extensions:
 - Mandatory: [Python](https://marketplace.visualstudio.com/items?itemName=ms-python.python), [Pylance](https://marketplace.visualstudio.com/items?itemName=ms-python.vscode-pylance), [Ruff](https://marketplace.visualstudio.com/items?itemName=charliermarsh.ruff), [Black](https://marketplace.visualstudio.com/items?itemName=ms-python.black-formatter), [ErrorLens](https://marketplace.visualstudio.com/items?itemName=usernamehw.errorlens)
 - Recommended: [Jupyter](https://marketplace.visualstudio.com/items?itemName=ms-toolsai.jupyter), [GitLens](https://marketplace.visualstudio.com/items?itemName=eamodio.gitlens)


## 5. Pull Request (PR) Checklist

Before requesting a review, ensure:

- [ ] The code runs locally without errors.

- [ ] No temporary print() or console.log() statements are left behind.

- [ ] The .gitignore has not been bypassed (no data files in the PR).

- [ ] New functions have docstrings explaining why, not just how.

## 6. Merging & Syncing

To avoid "Spaghetti History," we prefer Rebase over standard Merges for local syncing.

`git pull --rebase origin main`


If you encounter merge conflicts, resolve them in VS Code, then git rebase --continue.

Success for this prototype depends on our ability to iterate. Write clean code, but don't let "perfect" be the enemy of "shipped."