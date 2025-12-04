#!/usr/bin/env python3
"""Sample Python file for testing"""


def hello_world():
    print("Hello, World!")
    return "Hello"


def add_numbers(a, b):
    return a + b


if __name__ == "__main__":
    hello_world()
    result = add_numbers(1, 2)
    print(f"Result: {result}")
