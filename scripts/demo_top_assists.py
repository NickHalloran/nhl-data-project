import pandas as pd

from demo_all_stat_races import SKATER_STATS_PATH, additive_race


def main() -> None:
    additive_race(pd.read_parquet(SKATER_STATS_PATH), "assists", "top_assists.gif", "NHL Assist Leaders")


if __name__ == "__main__":
    main()