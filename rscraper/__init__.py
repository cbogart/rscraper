
from analyzeDeps import parseDESCRIPTION
from credentials import loadCredentials
from dbutil import getConnection
from extractGitPackages import extractGitWebscrape, extractGitDescription
from getRepoMetadata import getBioconductorWebscrape, getCranWebscrape
from getRepoMetadata import createMetadataTables, saveMetadata
from getRepoMetadata import getBioconductorDescription, getCranDescription
from gitscraper import queryRandomProject, queryParticularProject
from crossref import fillInDois, citationtext2doi, createSyntheticCitations
from scopus import findCanonicalFromDoi,  doScopusLookup
from utils import stripParentheticals, justAlphabetics, similar