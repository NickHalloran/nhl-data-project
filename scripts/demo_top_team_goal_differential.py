import pandas as pd

from demo_all_stat_races import TEAM_STATS_PATH, additive_race


def main() -> None:
    additive_race(
        pd.read_parquet(TEAM_STATS_PATH),
        "goal_differential",
        "top_team_goal_differential.gif",
        "NHL Teams by Goal Differential",
        top_n=32,
    )


if __name__ == "__main__":
    main()