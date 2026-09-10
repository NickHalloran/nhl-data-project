import pandas as pd

from demo_all_stat_races import GOALIE_STATS_PATH, additive_race


def main() -> None:
    additive_race(
        pd.read_parquet(GOALIE_STATS_PATH),
        "goals_against",
        "top_goalie_goals_against.gif",
        "Goalies by Goals Against",
    )


if __name__ == "__main__":
    main()