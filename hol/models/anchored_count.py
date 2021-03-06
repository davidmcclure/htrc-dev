

import numpy as np

from functools import partial
from scipy.stats import chi2_contingency
from collections import OrderedDict

from sqlalchemy import Column, Integer, String, \
        PrimaryKeyConstraint, distinct

from sqlalchemy.sql import text, func

from hol import config
from hol.models import BaseModel, Count
from hol.utils import flatten_dict, sort_dict
from hol.corpus import Corpus
from hol.volume import Volume



class AnchoredCount(BaseModel):


    __tablename__ = 'anchored_count'

    __table_args__ = (
        PrimaryKeyConstraint('token', 'year', 'anchor_count'),
    )

    token = Column(String, nullable=False)

    year = Column(Integer, nullable=False)

    anchor_count = Column(Integer, nullable=False)

    count = Column(Integer, nullable=False)


    @classmethod
    def flush(cls, counts):

        """
        Flush a set of counts to disk.

        Args:
            counts (dict): year -> level -> token -> count
        """

        session = config.Session()

        # SQLite "upsert."
        query = text("""

            INSERT OR REPLACE INTO {table!s} (
                token,
                year,
                anchor_count,
                count
            )

            VALUES (
                :token,
                :year,
                :anchor_count,
                :count + COALESCE(
                    (
                        SELECT count FROM {table!s} WHERE (
                            token = :token AND
                            year = :year AND
                            anchor_count = :anchor_count
                        )
                    ),
                    0
                )
            )

        """.format(table=cls.__tablename__))

        for year, level, token, count in flatten_dict(counts):

            session.execute(query, dict(
                token=token,
                year=year,
                anchor_count=level,
                count=count,
            ))

        session.commit()


    @classmethod
    def token_year_level_count(cls, token, year, level):

        """
        How many times did token X appear in year Y on pages where the anchor
        token appeared Z times?

        Args:
            token (str)
            year (int)
            level (int)

        Returns: int
        """

        with config.get_session() as session:

            res = (
                session
                .query(func.sum(cls.count))
                .filter(
                    cls.token==token,
                    cls.year==year,
                    cls.anchor_count==level,
                )
            )

            return res.scalar() or 0


    @classmethod
    def year_count_series(cls, year1, year2):

        """
        Get total token counts for a range of years.

        Args:
            year1 (int)
            year2 (int)

        Returns: OrderedDict {year: count, ...}
        """

        with config.get_session() as session:

            res = (
                session
                .query(cls.year, func.sum(cls.count))
                .filter(cls.year >= year1, cls.year <= year2)
                .group_by(cls.year)
                .order_by(cls.year)
            )

            return OrderedDict(res.all())


    @classmethod
    def token_counts_by_year_and_level(cls, year1=None, year2=None,
        level1=None, level2=None):

        """
        Given a year and level (or a range of either), map token -> count for
        tokens that appear on pages with the anchor token.

        Args:
            year1 (int)
            year2 (int)
            level1 (int)
            level2 (int)

        Returns: dict {token: count, ...}
        """

        with config.get_session() as session:

            query = session.query(cls.token, func.sum(cls.count))

            if year1:
                query = query.filter(cls.year >= year1)

            if year2:
                query = query.filter(cls.year <= year2)

            if level1:
                query = query.filter(cls.anchor_count >= level1)

            if level2:
                query = query.filter(cls.anchor_count <= level2)

            res = query.group_by(cls.token)

            return dict(res.all())


    @classmethod
    def total_count_by_year_and_level(cls, year1=None, year2=None,
        level1=None, level2=None):

        """
        Given a year and level (or a range of either), get the total number of
        tokens that appeared on pages with the anchor.

        Args:
            year1 (int)
            year2 (int)
            level1 (int)
            level2 (int)

        Returns: int
        """

        with config.get_session() as session:

            query = session.query(func.sum(cls.count))

            if year1:
                query = query.filter(cls.year >= year1)

            if year2:
                query = query.filter(cls.year <= year2)

            if level1:
                query = query.filter(cls.anchor_count >= level1)

            if level2:
                query = query.filter(cls.anchor_count <= level2)

            return query.scalar() or 0



    @classmethod
    def mdw(cls, year1=None, year2=None, level1=None, level2=None):

        """
        Given a range of years and levels, get a ranking of tokens in terms of
        their distinctiveness with the anchor.

        Args:
            year1 (int)
            year2 (int)
            level1 (int)
            level2 (int)

        Returns: OrderedDict {token: score, ...}
        """

        a = cls.token_counts_by_year_and_level(year1, year2, level1, level2)

        b = Count.token_counts_by_year(year1, year2)

        c = cls.total_count_by_year_and_level(year1, year2, level1, level2)

        d = Count.total_count_by_year(year1, year2)

        topn = dict()

        for token in a.keys():

            rc = np.array([
                [a[token], b[token]-a[token]],
                [c, d-c],
            ])

            g, _, _, _ = chi2_contingency(rc, lambda_='log-likelihood')

            topn[token] = g

        return sort_dict(topn)
