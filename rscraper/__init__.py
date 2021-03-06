
from analyzeDeps import parseDESCRIPTION
from credentials import loadCredentials
from dbutil import getConnection
from extractGitPackages import makeGitPseudoWebscrape, extractGitDescription
from getRepoMetadata import getBioconductorWebscrape, getCranWebscrape
from getRepoMetadata import createMetadataTables, saveMetadata, clearTaskViews
from getRepoMetadata import getBioconductorDescription, getCranDescription
from gitscraper import queryRandomProject, queryParticularProject, identifyNewProjects, CaughtUpException, createFreshGitprojectsTable, getCranHistoricalDependencies
from crossref import fillInDois, citationtext2doi, createSyntheticCitations
from scopus import findCanonicalFromDoi,  doScopusLookup, enable_scopus_proxy
from utils import stripParentheticals, justAlphabetics, similar, jmemo, urlmemo
from findAuthors import findAuthors
from downloadscrape import downloadLatestRstudioLogs
from parseDCF import parseDCF, DCFparse2DependencyLists, DCFFormatError
