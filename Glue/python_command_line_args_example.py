import sys

print("===============")
print(sys.argv)
print("===============")

# Check if exactly 2 arguments are passed
if len(sys.argv) != 3:
    print("Usage: python script.py <arg1> <arg2>")
    sys.exit(1)


arg1 = sys.argv[1]
arg2 = sys.argv[2]

print(f"Argument 1: {arg1}")
print(f"Argument 2: {arg2}")