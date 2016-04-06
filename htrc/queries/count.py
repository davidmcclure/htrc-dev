

from sqlalchemy.sql import func

from htrc import config
from htrc.models import Count


class CountQueries:


    def __init__(self):

        """
        Initialize a session.
        """

        self.session = config.Session()


    def years(self):

        """
        Get an ordered list of years.

        Returns: list<int>
        """

        res = (
            self.session
            .query(Count.year)
            .distinct()
            .order_by(Count.year.asc())
        )

        return [r[0] for r in res]


    def tokens(self):

        """
        Get an ordered list of all tokens.

        Returns: list<int>
        """

        res = (
            self.session
            .query(Count.token)
            .distinct()
            .order_by(Count.token.asc())
        )

        return [r[0] for r in res]


    def year_count(self, year):

        """
        Get the total token count for a year.

        Args:
            year (int)

        Returns: int
        """

        res = (
            self.session
            .query(func.sum(Count.count))
            .filter(Count.year==year)
        )

        return res.scalar() or 0


    def token_year_count(self, token, year):

        """
        How many times did token X appear in year Y?

        Args:
            token (str)
            year (int)

        Returns: int
        """

        res = (
            self.session
            .query(func.sum(Count.count))
            .filter(Count.token==token, Count.year==year)
        )

        return res.scalar() or 0


    def token_year_wpm(self, token, year):

        """
        How many times did token X appear per million words in year Y?

        Args:
            token (str)
            year (int)

        Returns: float
        """

        year_count = self.year_count(year)

        if year_count > 0:

            # Normalize per-M ratio.
            token_count = self.token_year_count(token, year)
            return (1e6 * token_count) / year_count

        else: return 0