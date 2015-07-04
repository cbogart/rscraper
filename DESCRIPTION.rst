rscraper: Scrape metadata about R projects on Github
====================================================

Utility functions for periodically querying Github for new or changed
R projects to see what R packages they use.  Also scrapes information
from other sources, including CRAN, Bioconductor, and Scopus

Contains DCF parsing capability (i.e. the DESCRIPTION file) that 
should probably be split off into its own projects.

Creates an sqlite database to hold data it finds.
