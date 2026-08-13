import argparse

def main():
    p = argparse.ArgumentParser()
    p.add_argument("--date", required=True)
    args = p.parse_args()
    print(f"Screen placeholder for {args.date}. Connect normalized data to strategies.")

if __name__ == "__main__":
    main()
