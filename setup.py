from setuptools import setup, find_packages
from setuptools.command.install import install
import subprocess


class PostInstallCommand(install):
    """Post-installation for installation mode."""

    def run(self):
        install.run(self)
        # Call your function here
        set_git_alias()


def set_git_alias():
    try:
        subprocess.check_call(
            ["git", "config", "--global", "alias.commit-auto", "!git-auto-commit"]
        )
        print("Git alias 'commit-auto' has been set.")
    except subprocess.CalledProcessError:
        print("Failed to set Git alias. Please set it manually.")


setup(
    name="git_auto_commit",
    version="0.1.0",
    author="Gianluigi Mucciolo",
    author_email="your_email@example.com",  # Replace with your email
    description="A Git extension to automatically generate commit messages.",
    long_description=open("README.md").read(),
    long_description_content_type="text/markdown",
    url="https://github.com/yourusername/git_auto_commit",  # Replace with the URL of your project
    packages=find_packages(),
    cmdclass={
        "install": PostInstallCommand,
    },
    entry_points={
        "console_scripts": [
            "git-auto-commit=git_auto_commit.main:main",
        ],
    },
    install_requires=["GitPython", "boto3", "langchain", "huggingface_hub", "pydantic"],
    classifiers=[
        "Development Status :: 3 - Alpha",
        "Intended Audience :: Developers",
        "Topic :: Software Development :: Version Control :: Git",
        "License :: OSI Approved :: MIT License",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.7",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
    ],
    python_requires=">=3.7",
    keywords="git commit automation",
)
