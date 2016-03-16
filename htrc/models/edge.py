

from clint.textui import progress
from sqlalchemy import Column, Integer, String
from sqlalchemy.schema import Index

from htrc import config
from htrc.models import Base


class Edge(Base):


    __tablename__ = 'edge'

    id = Column(Integer, primary_key=True)

    token1 = Column(String, nullable=False, index=True)

    token2 = Column(String, nullable=False, index=True)

    year = Column(Integer, nullable=False)

    weight = Column(Integer, nullable=False)


    @classmethod
    def index_corpus(cls, corpus, token, *args, **kwargs):

        """
        Index edges from a corpus.

        Args:
            corpus (Corpus)
            token (str)
        """

        volumes = progress.bar(
            corpus.volumes(),
            expected_size=len(list(corpus.paths()))
        )

        for volume in volumes:
            cls.index_volume(volume, token, *args, **kwargs)

        return graph


    @classmethod
    def index_volume(cls, volume, token, *args, **kwargs):

        """
        Index edges from a volume.

        Args:
            volume (Volume)
            token (str)
        """

        graph = volume.token_graph(token, *args, **kwargs)

        session = config.Session()

        for t1, t2, data in graph.edges_iter(data=True):

            weight = data.get('weight')

            # Try to update an existing edge.

            updated = session.query(cls).filter_by(

                token1=t1,
                token2=t2,
                year=volume.year,

            ).update(dict(
                weight = cls.weight + weight
            ))

            # If no rows updated, initialize the edge.

            if updated == 0:

                edge = cls(
                    token1=t1,
                    token2=t2,
                    year=volume.year,
                    weight=weight,
                )

                session.add(edge)

        session.commit()


# Unique index on the token pair.
Index(
    'ix_edge_token1_token2_year',
    Edge.token1,
    Edge.token2,
    Edge.year,
    unique=True,
)
