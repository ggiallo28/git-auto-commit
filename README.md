# Git Auto Commit

## Overview
`git_auto_commit` is a Git extension designed to automatically generate commit messages using advanced language models. By analyzing the changes in your Git repository, it crafts human-readable and contextually relevant commit messages, streamlining your development workflow.

## Features
- **Automatic Commit Message Generation**: Leverages Langchain's Large Language Models (LLMs) to generate commit messages based on the Git diff.
- **Easy Integration**: Seamlessly integrates with your Git workflow.
- **Customizable**: Allows for customization and manual override, ensuring flexibility in your commit message conventions.

## Installation
1. **Clone the Repository**:
   ```bash
   git clone https://github.com/ggiallo28/git-auto-commit
   ```
2. **Navigate to the Directory**:
   ```bash
   cd git_auto_commit
   ```
3. **Install the Package**:
   ```bash
   python setup.py install
   ```

## Usage
Once installed, `git_auto_commit` can be invoked through the `git auto-commit` alias. This will trigger the automatic generation of a commit message for your current repository changes.

### Example Usage
1. Make changes to your repository.
2. Stage your changes:
   ```bash
   git add .
   ```
3. Run `git_auto_commit`:
   ```bash
   git git auto-commit
   ```

## License
`git_auto_commit` is released under the MIT License. See the LICENSE file for more details.

