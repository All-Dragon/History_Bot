from sqlalchemy.dialects.postgresql import ENUM as PG_ENUM

roles = ("Ученик", "Преподаватель", "Админ")
user_role_enum = PG_ENUM(*roles, name="user_role")

question_types = ("multiple_choice", "free_text")
question_types_enum = PG_ENUM(*question_types, name="question_type")

test_status_enum = PG_ENUM(
    "draft",
    "published",
    "archived",
    name="test_status",
)

attempt_status_enum = PG_ENUM(
    "in_progress",
    "finished",
    "cancelled",
    name="attempt_status",
)
