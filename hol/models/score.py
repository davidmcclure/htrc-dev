

import numpy as np

from scipy.stats import chi2_contingency
from collections import OrderedDict

from sqlalchemy import Column, Integer, String, Float, PrimaryKeyConstraint

from hol import config
from hol.models import Base, Count, AnchoredCount


class Score(Base):


    __tablename__ = 'score'

    __table_args__ = (
        PrimaryKeyConstraint('token', 'year'),
    )

    token = Column(String, nullable=False)

    year = Column(Integer, nullable=False)

    score = Column(Float, nullable=False)


    @classmethod
    def index(cls, years):

        """
        Index log-likelihood scores.

        Args:
            years (iter)
        """

        session = config.Session()

        # Clear existing rows.
        session.query(cls).delete()

        yc0 = AnchoredCount.year_count_series(years)
        yc1 = Count.year_count_series(years)

        for year in years:

            c = yc0.get(year, 0)
            d = yc1.get(year, 0)

            tc0 = AnchoredCount.token_counts_by_year(year)
            tc1 = Count.token_counts_by_year(year)

            for token in tc0.keys():

                a = tc0.get(token, 0)
                b = tc1.get(token, 0)

                score, p, dof, exp = chi2_contingency(
                    np.array([[a, b], [c, d]]),
                    lambda_='log-likelihood',
                )

                session.add(cls(
                    token=token,
                    year=year,
                    score=score,
                ))

            print(year)

        session.commit()


    @classmethod
    def topn_by_year(cls, year, n):

        """
        Get the top N tokens for a year.

        Returns: [(token, rank), ...]
        """

        with config.get_session() as session:

            ranks = OrderedDict()

            res = (
                session
                .query(cls.token, cls.score)
                .filter(cls.year==year)
                .order_by(cls.score.desc())
                .limit(n)
            )

            for i, (token, rank) in enumerate(res):
                ranks[token] = i+1

            return ranks
