#!/usr/bin/env python3
# main.py - Entry point for Agent system

import os

from agents import UserAgent

WORKSPACE = os.path.expanduser("~/.agent0")


def main():
    agent = UserAgent(workspace=WORKSPACE)
    agent.run()


if __name__ == "__main__":
    main()
