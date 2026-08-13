import argparse
from data.providers.akshare_provider import AKShareProvider

def main():
    p = argparse.ArgumentParser()
    p.add_argument("--date", required=True)
    args = p.parse_args()
    provider = AKShareProvider()
    df = provider.limit_up_pool(args.date)
    print(df.head(20).to_string(index=False))

if __name__ == "__main__":
    main()
