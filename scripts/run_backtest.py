import argparse

def main():
    p = argparse.ArgumentParser()
    p.add_argument("--start", required=True)
    p.add_argument("--end", required=True)
    args = p.parse_args()
    print(f"Backtest placeholder: {args.start} -> {args.end}")

if __name__ == "__main__":
    main()
