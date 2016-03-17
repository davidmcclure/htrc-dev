

import re
import networkx as nx

from itertools import combinations
from collections import Counter
from stop_words import get_stop_words
from wordfreq import word_frequency

from htrc.term_graph import TermGraph


class Page:


    def __init__(self, json):

        """
        Wrap an individual page.

        Args:
            json (dict)
        """

        self.json = json


    @property
    def token_count(self):

        """
        Get the total number of "body" tokens.

        Returns: int
        """

        return self.json['body']['tokenCount']


    def total_counts(self, min_freq=1e-05):

        """
        Count the total occurrences of each unique token.

        Args:
            min_freq (float): Ignore words below this frequency.

        Returns: Counter
        """

        # Filter out non-letters.
        letters = re.compile('^[a-z]+$')

        # Get a stopword list.
        stop_words = get_stop_words('en')

        counts = Counter()
        for token, pc in self.json['body']['tokenPosCount'].items():

            token = token.lower()

            # Ignore irregular tokens.
            if not letters.match(token):
                continue

            # Ignore stopwords.
            if token in stop_words:
                continue

            # Ignore infrequent words.
            if word_frequency(token, 'en') < min_freq:
                continue

            counts[token] += sum(pc.values())

        return counts


    def graph(self, *args, **kwargs):

        """
        Assemble the page-level co-occurrence graph for all tokens.

        Returns: TermGraph
        """

        graph = TermGraph()

        counts = self.total_counts(*args, **kwargs)

        for (t1, c1), (t2, c2) in combinations(counts.items(), 2):
            graph.add_edge(t1, t2, weight=min(c1, c2))

        return graph


    def has_token(self, token):

        """
        Does the page contain a given token?

        Args:
            token (str)

        Returns: bool
        """

        return token in self.json['body']['tokenPosCount']
