import pandas as pd

from demo_all_stat_races import GOALIE_STATS_PATH, save_percentage_race


def main() -> None:
    save_percentage_race(pd.read_parquet(GOALIE_STATS_PATH))


if __name__ == "__main__":
    main()