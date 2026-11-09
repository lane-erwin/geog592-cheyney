import argparse
#argparse lets you put a description of ur code. also lets you put defaults. also help

def say_hello(name, times):
    for i in range(times):
        print(f"Hello, {name}!")

def main():
    parser = argparse.ArgumentParser(
        description= "A program that greets someone"
    )
    parser.add_argument("name", help="Name of the person to greet")
    parser.add_argument(
        "--times", type=int, default=1,
        help="Number of greetings (default: 1)"
    )
    args = parser.parse_args()

    say_hello(args.name, args.times)

if __name__ == "__main__":
    main()