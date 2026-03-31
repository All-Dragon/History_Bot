from .answers import answers_router
from .auth import authorization_router
from .bans import bans_router
from .questions import questions_router
from .stats import stats_router
from .users import users_router

__all__ = ['answers_router',
           'authorization_router',
           'bans_router',
           'questions_router',
           'stats_router',
           'users_router',
           ]