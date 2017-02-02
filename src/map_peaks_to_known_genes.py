import sys

from optparse import OptionParser

import numpy as np
import pandas as pd

from intervaltree import Interval, IntervalTree


usage = '%prog [options] <knownGene file> <peaks file>'
description = """
Map the peaks in <peaks file> to genes in <knownGene file>.  <knownGene file> is format is as
specified in http://hgdownload.cse.ucsc.edu/goldenPath/hg19/database/knownGene.sql, though BED
format is also accepted. <peaks file> format is as produced by GPS, MACS or BED.  If *auto* is
chosen (default) file extension is examined for *.xls* for default MACS format, *.txt* for GPS,
or *.bed* for BED format.
"""
parser = OptionParser(usage=usage, description=description, epilog='')#, formatter=MultiLineHelpFormatter())

parser.add_option('--upstream-window', dest='upstream_window', type='int', default=100000,
	help='window width in base pairs to consider promoter region [default: %default]')
parser.add_option('--downstream-window', dest='downstream_window', type='int', default=0,
	help='window width in base pairs to consider downstream region [default: %default]')
parser.add_option('--tss', dest='tss', action='store_true', default=False,
	help='calculate downstream window from transcription start site instead of transcription end site')
parser.add_option('--map-output', dest='peak_output', default=None,
	help='filename to output mapped peaks to [default: stdout]')
parser.add_option('--stats-output', dest='stats_output', default=sys.stderr,
	help='filename to output summary stats in conversion [default: stderr]')

parser.add_option('--intergenic', dest='intergenic', action='store_true',
	help='write intergenic peaks to the gene file as well with None as gene ID')
parser.add_option('--symbol-xref', dest='symbol_xref', default=None,
	help='Provide kgXref table file supplied to find a gene symbol and add as second column of output')



# if __name__ == '__main__':

# 	options, args = parser.parse_args(sys.argv[1:])
# 	if len(args) != 2: parser.error('Must provide two filename arguments')

# 	map_peaks_to_known_genes(args[0], args[1], options)


######################################## File Parsing Logic #######################################


def parse_known_genes_file(filepath):
	"""

	The known genes file format is the following:
	http://hgdownload.cse.ucsc.edu/goldenPath/hg19/database/knownGene.sql

	`name` varchar(255) NOT NULL DEFAULT '',
	`chrom` varchar(255) NOT NULL DEFAULT '',
	`strand` char(1) NOT NULL DEFAULT '',
	`txStart` int(10) unsigned NOT NULL DEFAULT '0',
	`txEnd` int(10) unsigned NOT NULL DEFAULT '0',
	`cdsStart` int(10) unsigned NOT NULL DEFAULT '0',
	`cdsEnd` int(10) unsigned NOT NULL DEFAULT '0',
	`exonCount` int(10) unsigned NOT NULL DEFAULT '0',
	`exonStarts` longblob NOT NULL,
	`exonEnds` longblob NOT NULL,
	`proteinID` varchar(40) NOT NULL DEFAULT '',
	`alignID` varchar(255) NOT NULL DEFAULT '',
	"""

	known_genes_fieldnames = ["name","chrom","strand","txStart","txEnd","cdsStart","cdsEnd","exonCount","exonStarts","exonEnds","proteinID","alignID"]

	known_genes_dataframe = pd.read_csv(filepath, delimiter='\t', names=known_genes_fieldnames, skipinitialspace=True)

	return known_genes_dataframe


def parse_peaks_file(filepath):
	"""
	My contract is that I will return to you an instance of Peaks, independent of the filetype you supply me

	BED:

	chrom - The name of the chromosome (e.g. chr3, chrY, chr2_random) or scaffold (e.g. scaffold10671).
	chromStart - The starting position of the feature in the chromosome or scaffold. The first base in a chromosome is numbered 0.
	chromEnd - The ending position of the feature in the chromosome or scaffold. The chromEnd base is not included in the display of the feature. For example, the first 100 bases of a chromosome are defined as chromStart=0, chromEnd=100, and span the bases numbered 0-99.

	The 9 additional optional BED fields are:

	name - Defines the name of the BED line. This label is displayed to the left of the BED line in the Genome Browser window when the track is open to full display mode or directly to the left of the item in pack mode.
	score - A score between 0 and 1000. If the track line useScore attribute is set to 1 for this annotation data set, the score value will determine the level of gray in which this feature is displayed (higher numbers = darker gray). This table shows the Genome Browser's translation of BED score values into shades of gray:
	strand - Defines the strand. Either "." (=no strand) or "+" or "-".
	thickStart - The starting position at which the feature is drawn thickly (for example, the start codon in gene displays). When there is no thick part, thickStart and thickEnd are usually set to the chromStart position.
	thickEnd - The ending position at which the feature is drawn thickly (for example, the stop codon in gene displays).
	itemRgb - An RGB value of the form R,G,B (e.g. 255,0,0). If the track line itemRgb attribute is set to "On", this RBG value will determine the display color of the data contained in this BED line. NOTE: It is recommended that a simple color scheme (eight colors or less) be used with this attribute to avoid overwhelming the color resources of the Genome Browser and your Internet browser.
	blockCount - The number of blocks (exons) in the BED line.
	blockSizes - A comma-separated list of the block sizes. The number of items in this list should correspond to blockCount.
	blockStarts - A comma-separated list of block starts. All of the blockStart positions should be calculated relative to chromStart. The number of items in this list should correspond to blockCount.


	"""

	# if peaks file format is BED

	peaks_fieldnames = ["chrom","chromStart","chromEnd","name","score","strand","thickStart","thickEnd","itemRgb","blockCount","blockSizes","blockStarts"]

	peaks_dataframe = pd.read_csv(filepath, delimiter='\t', names=peaks_fieldnames, skipinitialspace=True)

	# if peaks file format is MACS


	# if peaks file format is GPS


	return peaks_dataframe


def parse_kgXref_file(filepath):
	"""
	"""

	kgXref_fieldnames = ['kgID','mRNA','spID','spDisplayID','geneSymbol','refseq','protAcc','description']

	kgXref_dataframe = pd.read_csv(filepath, delimiter='\t', names=kgXref_fieldnames, skipinitialspace=True)

	return kgXref_dataframe



############################################ App Logic ############################################


def map_peaks_to_known_genes(peaks_filepath, known_genes_filepath, options): # kgXref_filepath too?
	"""
	"""

	reference = parse_known_genes_file(known_genes_filepath)
	peaks = parse_peaks_file(peaks_filepath)
	# kgXref = parse_kgXref_file(kgXref_filepath)

	build_search_window_around_reference_gene_transcription_start_sites(reference, options)

	reference = group_by_chromosome(reference)
	peaks = group_by_chromosome(peaks)

	peaks = {chrom: IntervalTree_from_dataframe(chromosome_peaks) for chrom, chromosome_peaks in peaks}
	reference = {chrom: IntervalTree_from_dataframe(gene_regions) for chrom, gene_regions in reference}

	peaks_with_associated_genes = map_peaks_to_reference(peaks, reference, options)

	output(peaks_with_associated_genes, options)


def build_search_window_around_reference_gene_transcription_start_sites(reference, options):
	"""
	parameters
	----------
		- reference is a dataframe
		- options are options which shall be unpacked here
	"""

	upstream_window = options.upstream_window
	downstream_window = options.downstream_window
	tss = options.tss





def group_by_chromosome(dataframe):
	"""
	Must be a dataframe with a chrom column
	"""

	return dict(list(dataframe.groupby('chrom')))


def IntervalTree_from_dataframe(dataframe):
	"""
	The parameter is a dataframe
	"""

	intervals = zip(dataframe.chromStart.values, dataframe.chromEnd.values, dataframe.values.tolist())

	tree = IntervalTree.from_tuples(intervals)

	return tree


def map_peaks_to_reference(peaks, reference, options):
	"""
	parameters
	----------
		- peaks is a dictionary of {chrom: IntervalTree}
		- reference is a dictionary of {chrom: IntervalTree}
		- options are options which shall be unpacked here
	"""

	upstream_window = options.upstream_window
	downstream_window = options.downstream_window
	tss = options.tss

	# so we have an upstream window and a downstream window.
	# the peaks file has no notion of upstream or downstream

	# so the question is really, given a TSS point in the known genes file
	# you can construct a window, upstream and downstream
	# and you want to ask, does a peak overlap with this at all.


	# we want to know whether there's a gene upstream or downstream


def output(peaks_with_associated_genes, options):
	"""
	parameters
	----------
		- options are options which shall be unpacked here

	"""

	peak_output = options.peak_output
	stats_output = options.stats_output



########################################### Error Logic ###########################################



peaks = parse_peaks_file("/Users/alex/Documents/OmicsIntegrator/example/a549/A549_FOXA1_broadPeak.bed")

peaks = group_by_chromosome(peaks)

tree = IntervalTree_from_dataframe(peaks.get('chr1'))


