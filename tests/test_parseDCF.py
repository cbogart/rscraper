# -*- coding: UTF-8 -*-
import unittest
from nose.plugins.attrib import attr
import rscraper
from rscraper.dbutil import *
import json
import os
import inspect
from rscraper.parseDCF import *
from rscraperTesting import RscraperTesting



DCF1 = """
Package: aBioMarVsuit
Type: Package
Title: A Biomarker Validation Suit for predicting Survival using gene
        signature.
Version: 1.0
Date: 2012-12-26
Author: Pushpike Thalikarathne and Ziv Shkedy
Maintainer: Pushpike Thalikarathne <Pushpike@gmail.com>
Description: This package is useful in finding and validating
        predictive gene signature for classifying low risk versus high
        risk patients in early phase clinical trials.  The primary end
        point is survival, and classification of cancer patients into
        low risk or high risk groups is mainly based on median cutoff,
        but others can be considered as well. It can also accommodate
        the prognostic factors if any. Both statistical and machine
        learning techniques are integrated as validating suit.  The
        package can be used to perform the analysis using the entire
        samples and can also be used to carryout large scale cross
        validations. For the first instance, package reduces larger
        gene expression matrix to smaller version using supervised
        principle components analysis. Later entire validation
        procedure can be performed using reduced gene expression matrix
        with various types of validation schemes.
Depends: glmnet, graphics, gplots, pls, survival, DLBCL, superpc,
        utils, methods, stats, Biobase
License: GPL-3
LazyLoad: yes
Packaged: 2013-01-14 21:31:11 UTC; lucp2520
Repository: CRAN
Date/Publication: 2013-01-15 08:00:31
"""

DCF2 = """
Package: knitr
Type: Package
Title: A general-purpose package for dynamic report generation in R
Version: 1.4
Date: 2013-08-10
Authors@R: c(person("Alastair", "Andrew", role = "ctb"),
    person("Alex", "Zvoleff", role = "ctb"),
    person("Brian", "Diggs", role = "ctb"),
    person("Cassio", "Pereira", role = "ctb"),
    person("Hadley", "Wickham", role = "ctb"),
    person("Heewon", "Jeon", role = "ctb"),
    person("Jeff", "Arnold", role = "ctb"),
    person("Jeremy", "Stephens", role = "ctb"),
    person("Jim", "Hester", role = "ctb"),
    person("Joe", "Cheng", role = "ctb"),
    person("Jonathan", "Keane", role = "ctb"),
    person("J.J.", "Allaire", role = "ctb"),
    person("Johan", "Toloe", role = "ctb"),
    person("Kohske", "Takahashi", role = "ctb"),
    person("Michel", "Kuhlmann", role = "ctb"),
    person("Nacho", "Caballero", role = "ctb"),
    person("Nick", "Salkowski", role = "ctb"),
    person("Noam", "Ross", role = "ctb"),
    person("Ramnath", "Vaidyanathan", role = "ctb"),
    person("Richard", "Cotton", role = "ctb"),
    person("Sietse", "Brouwer", role = "ctb"),
    person("Simon", "de Bernard", role = "ctb"),
    person("Taiyun", "Wei", role = "ctb"),
    person("Thibaut", "Lamadon", role = "ctb"),
    person("Tom", "Torsney-Weir", role = "ctb"),
    person("Trevor", "Davis", role = "ctb"),
    person("Weicheng", "Zhu", role = "ctb"),
    person("Wush", "Wu", role = "ctb"),
    person("Yihui", "Xie", email = "xie@yihui.name", role = c("aut", "cre")))
Author: Yihui Xie
Maintainer: Yihui Xie <xie@yihui.name>
Description: This package provides a general-purpose tool for dynamic report
    generation in R, which can be used to deal with any type of (plain text)
    files, including Sweave, HTML, Markdown, reStructuredText and AsciiDoc. The
    patterns of code chunks and inline R expressions can be customized. R code
    is evaluated as if it were copied and pasted in an R terminal thanks to the
    evaluate package (e.g. we do not need to explicitly print() plots from
    ggplot2 or lattice). R code can be reformatted by the formatR package so
    that long lines are automatically wrapped, with indent and spaces being
    added, and comments being preserved. A simple caching mechanism is provided
    to cache results from computations for the first time and the computations
    will be skipped the next time. Almost all common graphics devices,
    including those in base R and add-on packages like Cairo, cairoDevice and
    tikzDevice, are built-in with this package and it is straightforward to
    switch between devices without writing any special functions. The width and
    height as well as alignment of plots in the output document can be
    specified in chunk options (the size of plots for graphics devices is still
    supported as usual). Multiple plots can be recorded in a single code chunk,
    and it is also allowed to rearrange plots to the end of a chunk or just
    keep the last plot. Warnings, messages and errors are written in the output
    document by default (can be turned off). Currently LaTeX, HTML, Markdown
    and reST are supported, and other output formats can be supported by hook
    functions. The large collection of hooks in this package makes it possible
    for the user to control almost everything in the R code input and output.
    Hooks can be used either to format the output or to run a specified R code
    fragment before or after a code chunk. The language in code chunks is not
    restricted to R only (there is simple support to Python and Awk, etc). Many
    features are borrowed from or inspired by Sweave, cacheSweave, pgfSweave,
    brew and decumar.
Depends: R (>= 2.14.1)
Imports: evaluate (>= 0.4.7), digest, formatR (>= 0.9), highr (>= 0.2),
        markdown (>= 0.6.3), stringr (>= 0.6), tools
Suggests: testit, rgl, codetools, R2SWF (>= 0.4), XML, RCurl
License: GPL
URL: http://yihui.name/knitr/
BugReports: https://github.com/yihui/knitr/issues
VignetteBuilder: knitr
Collate: 'package.R' 'utils-upload.R' 'plot.R' 'defaults.R' 'parser.R'
        'cache.R' 'pattern.R' 'output.R' 'block.R' 'hooks.R' 'utils.R'
        'highlight.R' 'themes.R' 'header.R' 'themes-eclipse.R'
        'concordance.R' 'engine.R' 'citation.R' 'hooks-chunk.R'
        'hooks-extra.R' 'hooks-latex.R' 'hooks-html.R' 'hooks-md.R'
        'hooks-rst.R' 'spin.R' 'utils-base64.R' 'utils-rd2html.R'
        'zzz.R' 'template.R' 'utils-sweave.R' 'utils-conversion.R'
        'utils-vignettes.R' 'pandoc.R' 'hooks-asciidoc.R' 'table.R'
        'rocco.R'
Packaged: 2013-08-10 00:12:07 UTC; yihui
NeedsCompilation: no
Repository: CRAN
Date/Publication: 2013-08-10 10:51:51
"""


class TestDCFs(RscraperTesting):

    @attr("dcf")
    def test_parse(self):
        dcfp1 = parseDCF(DCF1)
        self.assertEquals(dcfp1[0]["Depends"], "glmnet, graphics, gplots, pls, survival, DLBCL, superpc, utils, methods, stats, Biobase")
        self.assertEquals(dcfp1[0]["Repository"], "CRAN", "single line Depends")

        dcfp2 = parseDCF(DCF2)
        self.assertEquals(dcfp2[0]["Imports"], "evaluate (>= 0.4.7), digest, formatR (>= 0.9), highr (>= 0.2), markdown (>= 0.6.3), stringr (>= 0.6), tools")

    @attr("dcf")
    def test_collate_dcf_parses(self):
        dcfp1 = parseDCF(DCF1)
        dcfp2 = parseDCF(DCF2)
        (dc, dv) = DCFparse2DependencyLists(dcfp1 + dcfp2)
        print json.dumps(dc, indent=4)
        self.assertEquals(dc["knitr"]["1.4"], "2013-08-10")
        self.assertEquals(dc["aBioMarVsuit"]["1.0"], "2012-12-26")
        self.assertEquals(dv["knitr"]["1.4"]["evaluate"], [("Imports", ">= 0.4.7")])
        self.assertEquals(dv["knitr"]["1.4"]["stringr"], [("Imports", ">= 0.6")])
        self.assertEquals(dv["knitr"]["1.4"]["digest"], [("Imports", "")])
        self.assertEquals(dv["knitr"]["1.4"]["rgl"], [("Suggests", "")])
        self.assertEquals(dv["knitr"]["1.4"]["R2SWF"], [("Suggests", ">= 0.4")])


if __name__ == '__main__':
    unittest.main()
