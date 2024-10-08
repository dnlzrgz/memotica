# memotica

An easy, fast, and minimalist space repetition application for the terminal

![Main screen screenshot](./assets/memotica_tui.svg)

> When I started working on memotica, I had a few goals in mind. First, I wanted to become more familiar with textual. Second, I aimed to create an easy-to-use tool to meet my own needs for learning basic vocabulary in German and Japanese. However, over time, I became interested in other projects and began accepting professional opportunities again. As a result, I have been unable to invest as much time in memotica as I initially would have liked. That's why I am now archiving this project.

## Features

- Markdown support for flashcards.
- Support for sub-decks for a better organization.
- Advanced spaced repetition with the SM2 algorithm.
- Keyboard-First navigation.
- Easy to add, edit and delete decks and flashcards.
- Export and import your data.

## WIP

memotica is nearly ready for use, but there are some features that I would like to implement before reaching version `v1.0.0`:

- Basic statistics.
- Better flashcards management.
- Customizable space repetition algorithm.
- Interoperability with Anki.
- Themes.
- Visual indicators.

## Motivation

Recently, I began to study German and a bit of Japanese. At the same time I was also thinking of playing a bit more with [textual](https://textual.textualize.io/). After encountering some issues with the Anki application on Linux, I decided that it would be a great idea to create a similar application more tailored for my needs and usage.

## Screenshots

![Help modal](./assets/memotica_help.svg)
![Review Screen](./assets/memotica_review_answer.svg)

## Installation

> memotica automatically creates a directory in the most appropriate location based on your operating system. This directory contains a SQLite database where all your decks and flashcards are stored. You can learn more about how this is done [here](https://click.palletsprojects.com/en/8.1.x/api/#click.get_app_dir).

### Using `pip`

```bash
pip install memotica
```

### With `pipx` (recommended)

```bash
pipx install memotica
```

## Usage

### TUI

Once memotica is installed, you should have the `memotica` command available. To start the TUI simply run:

```bash
memotica
```

Or

```bash
memotica run
```

Once the TUI is displayed, you can:

- **Display the help message** by pressing `F1`.
- **Add a new deck** by pressing `ctrl+n`.
- **Add flashcards** with `ctrl+a`.

After you've added some flashcards, select a deck in the deck tree and press `ctrl+s` to begin the review process.

> In the review screen you can use `space`/`enter` to show the answer and `1`, `2`, `3` to mark the question as `Bad`, `Good` or `Easy`.

### Other commands

memotica provides commands to export and import your flashcards, decks and review information in the form of CSV files. To see all the available options run:

```bash
memotica export --help
```

And

```bash
memotica import --help
```

## Help is Welcome

If you have any suggestions or would like to contribute to this project, please feel free to open an issue. Thank for your interest!

## Thanks

I took inspiration and implement various aspects of memotica by reviewing and studying the source code from [harlequin.sh](https://harlequin.sh/).
