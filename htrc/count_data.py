

import os
import shelve

from multiprocessing import Pool
from contextlib import contextmanager

from htrc.corpus import Corpus
from htrc.volume import Volume
from htrc.utils import ensure_dir



class CountData:


    def __init__(self, path):

        """
        Canonicalize the root path.

        Args:
            path (str)
        """

        self.path = os.path.abspath(path)

        ensure_dir(self.path)


    @contextmanager
    def get_shelf(self, year):

        """
        Get a shelve data handle.

        Args:
            year (int)

        Yields: shelve.DbFilenameShelf
        """

        path = os.path.join(self.path, str(year))

        with shelve.open(path) as data:
            yield data


    def update_year(self, year, counts):

        """
        Merge counts into a year shelf.

        Args:
            year (int)
            counts (Counter)
        """

        with self.get_shelf(year) as data:
            for token, count in counts.items():

                # Update the count if the token has been seen.
                if token in data:
                    data[token] += count

                # Otherwise, initialize the counter.
                else:
                    data[token] = count


    def index(self, numprocs=8):

        """
        Index per-year counts.

        Args:
            numprocs (int)
        """

        corpus = Corpus.from_env()

        with Pool(numprocs) as pool:

            # Spool a job for each volume.
            jobs = pool.imap(get_vol_counts, corpus.paths())

            for i, (year, counts) in enumerate(jobs):
                self.update_year(year, counts)
                print(i)
