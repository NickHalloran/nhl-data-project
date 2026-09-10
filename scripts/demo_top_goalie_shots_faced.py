import pandas as pd

from demo_all_stat_races import GOALIE_STATS_PATH, additive_race


def main() -> None:
    additive_race(
        pd.read_parquet(GOALIE_STATS_PATH),
        "shots_faced",
        "top_goalie_shots_faced.gif",
        "Goalies by Shots Faced",
    )


if __name__ == "__main__":
    main()