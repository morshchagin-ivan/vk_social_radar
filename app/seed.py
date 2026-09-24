from __future__ import annotations

from datetime import date, timedelta

from .db import get_connection
from .message_stats import normalize_message_stats
from .snapshots import create_snapshot


def seed_demo_data() -> None:
    with get_connection() as conn:
        existing = conn.execute("SELECT COUNT(*) AS count FROM people").fetchone()["count"]
        # A valid empty or incomplete v2 capture is user history too.
        if existing or conn.execute("SELECT 1 FROM snapshots LIMIT 1").fetchone():
            return

        people = [
            (101, "Анна Петрова", "https://vk.com/id101", "", 0),
            (102, "Сергей Волков", "https://vk.com/id102", "", 0),
            (103, "Мария Орлова", "https://vk.com/id103", "", 0),
            (104, "Иван Крылов", "https://vk.com/id104", "", 0),
            (105, "Ольга Соколова", "https://vk.com/id105", "", 0),
            (106, "Дмитрий Лебедев", "https://vk.com/id106", "", 0),
        ]
        conn.executemany(
            """
            INSERT INTO people(vk_id, full_name, profile_url, avatar_url, is_deactivated)
            VALUES (?, ?, ?, ?, ?)
            """,
            people,
        )

        ids = {
            row["full_name"]: row["id"]
            for row in conn.execute("SELECT id, full_name FROM people").fetchall()
        }

        today = date.today()
        previous = today - timedelta(days=1)

        previous_friends = ["Анна Петрова", "Сергей Волков", "Мария Орлова", "Иван Крылов", "Ольга Соколова"]
        current_friends = ["Анна Петрова", "Сергей Волков", "Мария Орлова", "Дмитрий Лебедев"]

        previous_followers = ["Дмитрий Лебедев"]
        current_followers = ["Иван Крылов", "Ольга Соколова"]

        for relation, day, names in (
            ("friend", previous, previous_friends), ("friend", today, current_friends),
            ("follower", previous, previous_followers), ("follower", today, current_followers),
        ):
            create_snapshot({"relation_type": relation, "snapshot_date": day.isoformat(),
                "source": "synthetic_demo", "people": [
                    dict(vk_id=row[0], full_name=row[1], profile_url=row[2], avatar_url=row[3])
                    for row in people if row[1] in names]}, conn=conn)

        period_end = today
        period_start = today - timedelta(days=29)
        message_rows = [
            (ids["Анна Петрова"], 157, 129, 18, 8, 4, 11.0),
            (ids["Сергей Волков"], 23, 41, 9, 2, 7, 138.0),
            (ids["Мария Орлова"], 12, 57, 6, 1, 8, 540.0),
            (ids["Иван Крылов"], 4, 8, 3, 1, 2, 85.0),
            (ids["Ольга Соколова"], 0, 13, 2, 0, 2, None),
            (ids["Дмитрий Лебедев"], 19, 11, 5, 3, 2, 27.0),
        ]
        for person_id, incoming, outgoing, active_days, initiated_by_person, initiated_by_me, reply in message_rows:
            stats = normalize_message_stats({
                "period_start": period_start.isoformat(), "period_end": period_end.isoformat(),
                "incoming_count": incoming, "outgoing_count": outgoing,
                "active_days": active_days, "initiated_by_person": initiated_by_person,
                "initiated_by_me": initiated_by_me,
            })
            conn.execute(
                """
                INSERT INTO message_stats(
                    person_id, period_start, period_end, incoming_count, outgoing_count,
                    active_days, initiated_by_person, initiated_by_me, median_reply_minutes
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    person_id,
                    stats["period_start"],
                    stats["period_end"],
                    stats["incoming_count"],
                    stats["outgoing_count"],
                    stats["active_days"],
                    stats["initiated_by_person"],
                    stats["initiated_by_me"],
                    reply,
                ),
            )
