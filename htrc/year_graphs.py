

import os
import matplotlib.pyplot as plt

from collections import OrderedDict
from functools import lru_cache

from htrc.token_graph import TokenGraph
from htrc.utils import sort_dict_by_key


class YearGraphs:


    def __init__(self, path, source):

        """
        Canonicalize the root path.

        Args:
            path (str)
        """

        self.path = os.path.abspath(path)

        self.source = source


    @lru_cache()
    def years(self):

        """
        Generate years in the corpus

        Yields: int
        """

        years = []

        for entry in os.scandir(self.path):
            year = os.path.basename(entry.path)
            years.append(int(year))

        return sorted(years)


    def graph_by_year(self, year):

        """
        Hydrate the graph for a year.

        Args:
            year (int)

        Returns: TokenGraph
        """

        path = os.path.join(self.path, str(year))

        return TokenGraph.from_shelf(path)


    @lru_cache()
    def all_tokens(self):

        """
        Get a set of all tokens in the graphs.

        Returns: set
        """

        tokens = set()

        for entry in os.scandir(self.path):

            graph = TokenGraph.from_shelf(entry.path)
            tokens.update(graph.nodes())

        return tokens


    @lru_cache()
    def baseline_time_series(self):

        """
        Get the total per-year time series for all token weights.

        Returns: list of (year, value)
        """

        data = []

        for year in self.years():

            graph = self.graph_by_year(year)

            total = 0
            for t1, t2, d in graph.edges(data=True):
                total += d['weight']

            data.append((year, total))

        return data


    @lru_cache()
    def token_time_series(self, token):

        """
        Get the total per-year time series for an individual token.

        Returns: list of (year, value)
        """

        data = []

        for year in self.years():

            graph = self.graph_by_year(year)

            value = 0
            if graph.has_edge(self.source, token):
                value = graph[self.source][token]['weight']

            data.append((year, value))

        return data


    def plot_baseline_time_series(self):

        """
        Plot the baseline time series.
        """

        data = self.baseline_time_series()

        plt.plot(*zip(*data))
        plt.show()


    def plot_token_time_series(self, token):

        """
        Plot the time series for a token.
        """

        data = self.token_time_series(token)

        plt.plot(*zip(*data))
        plt.show()