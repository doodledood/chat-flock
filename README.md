# ChatFlock

<div align="center">

[![Build status](https://github.com/doodledood/chat-flock/workflows/build/badge.svg?branch=master&event=push)](https://github.com/doodledood/chat-flock/actions?query=workflow%3Abuild)
[![Python Version](https://img.shields.io/pypi/pyversions/chat-flock.svg)](https://pypi.org/project/chat-flock/)
[![Dependencies Status](https://img.shields.io/badge/dependencies-up%20to%20date-brightgreen.svg)](https://github.com/doodledood/chat-flock/pulls?utf8=%E2%9C%93&q=is%3Apr%20author%3Aapp%2Fdependabot)

[![Code style: black](https://img.shields.io/badge/code%20style-black-000000.svg)](https://github.com/psf/black)
[![Security: bandit](https://img.shields.io/badge/security-bandit-green.svg)](https://github.com/PyCQA/bandit)
[![Pre-commit](https://img.shields.io/badge/pre--commit-enabled-brightgreen?logo=pre-commit&logoColor=white)](.pre-commit-config.yaml)
[![Semantic Versions](https://img.shields.io/badge/%20%20%F0%9F%93%A6%F0%9F%9A%80-semantic--versions-e10079.svg)](https://github.com/doodledood/chat-flock/releases)
[![License](https://img.shields.io/github/license/chat-flock/chat-flock)](LICENSE)
![Coverage Report](assets/images/coverage.svg)

Driving Dynamic Multi-Participant Chat Interactions for AI and Human Discourse 🤖

</div>

## 📦 Installation

```bash
pip install -U chat-flock
```

or install with `Poetry`

```bash
poetry add chat-flock
```

## 🤔 What is this?

ChatFlock is a Python library that revolutionizes the way multi-participant chats are conducted by integrating Large Language Models (LLMs) at its core. Born from first principles design, it not only simplifies orchestrating complex chat scenarios but also introduces an innovative structure that mirrors organizational communication. 

At the heart of ChatFlock is the Conductor, a novel entity that determines the speaking order, enabling seamless coordination among AI and human participants. This orchestration allows for nuanced conversations and decision-making processes that go beyond traditional chat systems.

**NOTE: We are still in a very early and experimental stage of development, so the library might be unstable and the API might change relatively frequently. As soon as we reach a stable version, everything will get properly tested and documented.**

### 📝 Usage Examples 

#### 2-Participant Chat

- [Basic ChatGPT Clone](examples/chatgpt_clone.py)
- [Basic ChatGPT Clone with Tools](examples/chatgpt_clone_with_additional_tools.py)
- [Basic ChatGPT Clone with LangChain Memory](examples/chatgpt_clone_with_langchain_memory.py)
- [Basic ChatGPT Clone with LangChain-Based Retrieval](examples/chatgpt_clone_with_langchain_retrieval.py)

#### Multi-Participant Chat (Manual Setup)

- [3-Way Chat with an AI-based Conductor](examples/three_way_ai_conductor.py)
- [Multi-Participant Chat with a Group-Based Participant (Manual)](examples/manual_internal_group_participant.py)

#### Multi-Participant Chat (Automatically Composed)
- [Multi-Participant Chat with a Composition Generator with a 1-level Composition](examples/automatic_chat_simple_composition.py)
- [Multi-Participant Chat with a Composition Generator with a 2-Level Composition](examples/automatic_chat_simple_composition.py)
- [Multi-Participant Chat with a Composition Generator with a deep (3+ level) Hierarchical Composition](examples/automatic_hierarchical_chat_composition.py)

#### End-to-End Examples
- [BSHR (Brainstorm-Search-Hypothesize-Refine) Loop](chatflock/use_cases/bshr.py) - Based on [David Shapiro's](https://github.com/daveshap/BSHR_Loop) idea.

## 🚀 Features

- **Multi-Participant LLM-Based Chats**: Enable rich, collaborative conversations with AI and human participants.
- **Conductor Orchestration**: A unique system that manages turn-taking and dialogue flow, ensuring smooth chat progression.
- **Composition Generators**: Smart modules that configure AI participants to achieve specific conversational goals.
- **Group-Based Participants**: Implement sub-chats that handle complex queries internally before delivering concise responses.
- **Hierarchical Structure**: Create a scalable, organizational-like chat structure for complex task delegation and management.
- **Extensive LLM Toolkit Support**: Fully compatible with existing LLM ecosystems like LangChain, enhancing their features for a robust chat experience.
- **Web Research Module**: A sophisticated tool that conducts automated web research, leveraging selenium to analyze top search results.
- **BSHR (Brainstorm-Search-Hypothesize-Refine) Loop**: An integrated module that employs the automated research tool in a loop using information literacy techniques for superior research outcomes (based on how humans do research). Credit: [David Shapiro](https://github.com/daveshap/BSHR_Loop)
- **Code Execution Tools**: Facilitate the execution of code snippets within the chat, with support for both local and Docker environments.

## 🌟 What's Next?
- **Asynchronous Chat Support**: Plans to enable non-real-time conversations, allowing for more flexible interaction timelines.
- **OpenAI Assistant Integration**: Future updates will include compatibility with OpenAI's latest features, expanding the library's AI capabilities.
- **Enhanced Code Execution**: Upcoming versions will introduce advanced code execution features, including support for writing to files and more comprehensive execution environments.

## 💁 Contributing
As an open-source project in a rapidly developing field, we are extremely open to contributions, whether it be in the form of a new feature, improved infrastructure, or better documentation.

For detailed information on how to contribute, see [here](CONTRIBUTING.md).

## 📈 Releases

You can see the list of available releases on the [GitHub Releases](https://github.com/doodledood/chat-flock/releases) page.

We follow [Semantic Versions](https://semver.org/) specification.

We use [`Release Drafter`](https://github.com/marketplace/actions/release-drafter). As pull requests are merged, a draft release is kept up-to-date listing the changes, ready to publish when you’re ready. With the categories option, you can categorize pull requests in release notes using labels.

### List of labels and corresponding titles

|               **Label**               |  **Title in Releases**  |
| :-----------------------------------: | :---------------------: |
|       `enhancement`, `feature`        |       🚀 Features       |
| `bug`, `refactoring`, `bugfix`, `fix` | 🔧 Fixes & Refactoring  |
|       `build`, `ci`, `testing`        | 📦 Build System & CI/CD |
|              `breaking`               |   💥 Breaking Changes   |
|            `documentation`            |    📝 Documentation     |
|            `dependencies`             | ⬆️ Dependencies updates |

GitHub creates the `bug`, `enhancement`, and `documentation` labels for you. Dependabot creates the `dependencies` label. Create the remaining labels on the Issues tab of your GitHub repository, when you need them.

#### Building and releasing the package

Building a new version of the application contains steps:

- Bump the version of the package `poetry version <version>`. You can pass the new version explicitly, or a rule such as `major`, `minor`, or `patch`. For more details, refer to the [Semantic Versions](https://semver.org/) standard.
- Make a commit to `GitHub`.
- Create a `GitHub release`.
- And... publish 🙂 `poetry publish --build`

## 🛡 License

[![License](https://img.shields.io/github/license/chat-flock/chat-flock)](LICENSE)

This project is licensed under the terms of the `MIT` license. See [LICENSE](LICENSE) for more details.

## 📃 Citation

```bibtex
@misc{chat-flock,
  author = {doodledood},
  title = {Driving Dynamic Multi-Participant Chat Interactions for AI and Human Discourse},
  year = {2023},
  publisher = {GitHub},
  journal = {GitHub repository},
  howpublished = {\url{https://github.com/doodledood/chat-flock}}
}
```

## ❤️ Package Template Credits [![🚀 Your next Python package needs a bleeding-edge project structure.](https://img.shields.io/badge/python--package--template-%F0%9F%9A%80-brightgreen)](https://github.com/TezRomacH/python-package-template)

This project was generated with [`python-package-template`](https://github.com/TezRomacH/python-package-template)
