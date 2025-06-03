#!/usr/bin/env python3
import argparse
import sys

def set_terminal_title(title: str):
    sys.stdout.write(f"\33]0;{title}\a")
    sys.stdout.flush()

def main():
    parser = argparse.ArgumentParser(
        description="Set the terminal tab title using ANSI escape sequences."
    )
    parser.add_argument(
        "title",
        nargs="+",
        help="The new title for the terminal tab."
    )
    args = parser.parse_args()
    title = " ".join(args.title)
    set_terminal_title(title)

if __name__ == "__main__":
    main()
 
