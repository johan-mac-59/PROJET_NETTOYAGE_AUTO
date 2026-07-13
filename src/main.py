import os

def main():
    input_files = ["input.csv", "input.json"]
    for file in input_files:
        if file.endswith(".csv"):
            clean_csv(file, f"cleaned_{file}")
        elif file.endswith(".json"):
            clean_json(file, f"cleaned_{file}")

if __name__ == "__main__":
    main()