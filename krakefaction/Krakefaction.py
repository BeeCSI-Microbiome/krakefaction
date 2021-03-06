#!/usr/bin/env python

"""
# =============================================================================

Copyright Government of Canada 2018

Written by: Eric Marinier, Public Health Agency of Canada,
    National Microbiology Laboratory

Licensed under the Apache License, Version 2.0 (the "License"); you may not use
this file except in compliance with the License. You may obtain a copy of the
License at:

http://www.apache.org/licenses/LICENSE-2.0

Unless required by applicable law or agreed to in writing, software distributed
under the License is distributed on an "AS IS" BASIS, WITHOUT WARRANTIES OR
CONDITIONS OF ANY KIND, either express or implied. See the License for the
specific language governing permissions and limitations under the License.

# =============================================================================
"""

__version__ = '0.2.0'

import os
import argparse
import sys
import random

"""
# =============================================================================

GLOBALS

# =============================================================================
"""

PROGRAM_DESCRIPTION = "This program generates rarefaction data from Kraken \
    data. This tool was built against Kraken v0.10.5-beta."

PROGRAM_USAGE = "%(prog)s -u UNTRANSLATED -t TRANSLATED -o OUTPUT"

# CONSTANTS

CLASSIFIED = "C"

# DEFAULTS #

DEFAULT_RATE = 0.05

# ARGUMENTS #

LONG = "--"
SHORT = "-"

# REQUIRED ARGUMENTS #

UNTRANSLATED = "untranslated"
UNTRANSLATED_LONG = LONG + UNTRANSLATED
UNTRANSLATED_SHORT = SHORT + "u"
UNTRANSLATED_HELP = "The file name of the untranslated Kraken reads (the \
    default output of Kraken). This untranslated file may be filtered or \
    unfiltered. This file is generated by running 'kraken'."

TRANSLATED = "translated"
TRANSLATED_LONG = LONG + TRANSLATED
TRANSLATED_SHORT = SHORT + "t"
TRANSLATED_HELP = "The file name of the translated Kraken reads. This file is \
    generated by running 'kraken-translate'."

OUTPUT = "output"
OUTPUT_LONG = LONG + OUTPUT
OUTPUT_SHORT = SHORT + "o"
OUTPUT_HELP = "The file name of the rarefaction data output."

# OPTIONAL ARGUMENTS #

RATE = "rate"
RATE_LONG = LONG + RATE
RATE_SHORT = SHORT + "r"
RATE_HELP = "The sampling rate in the range (0, 1]. For example, a rate of \
    0.1 will generate 10 data points (0.1, 0.2, etc.)."

# Version number
VERSION = "version"
VERSION_LONG = LONG + VERSION
VERSION_SHORT = SHORT + "V"


"""
# =============================================================================

SAMPLE
------

PURPOSE
-------

This class represents a sample of reads from the entire input of reads.

# =============================================================================
"""
class Sample:

    # Principal Classification Rankings:
    DOMAIN = "d"
    PHYLUM = "p"
    CLASS = "c"
    ORDER = "o"
    FAMILY = "f"
    GENERA = "g"
    SPECIES = "s"
    SUBSPECIES = "s1"

    # Kraken:
    KRAKEN_SEPARATOR = "__"

    """
    # =========================================================================

    CONSTRUCTOR
    -----------


    INPUT
    -----

    [FLOAT] [rate]
        The sampling rate of this sample. This must be a number between (0, 1].

    # =========================================================================
    """
    def __init__(self, rate):

        self.rate = rate
        self.numberOfReads = 0

        self.domainDictionary = {}
        self.phylumDictionary = {}
        self.classDictionary = {}
        self.orderDictionary = {}
        self.familyDictionary = {}
        self.generaDictionary = {}
        self.speciesDictionary = {}
        self.subspeciesDictionary = {}

    """
    # =========================================================================

    UPDATE DICTIONARIES
    -------------------


    PURPOSE
    -------

    Updates the sample's dictionaries with the passed taxonomic rankings. These
    dictionaries maintain the unique principal classification rankings that
    have been observed. When a new taxonomic ranking is observed, it will be
    added to the appropriate dictionary. When a previously seen taxonomic
    ranking is observed, it will be ignored.


    INPUT
    -----

    [STRING LIST] [rankings]
        A list of strings corresponding to specific taxonomic rankings. The
        format of these strings must be consistant with Kraken's 'translation'
        output. These strings must start with a rank identifier (d, p, c, p, f,
        g, s), then two "_" characters ("__"), then the name ("Bacteria"). For
        example, "d__Bacteria" and "s__Prevotella_enoeca".


    RETURN
    ------

    [NONE]


    POST
    ----

    The principal classification ranking dictionaries will be updated,
    according to the passed [rankings].

    # =========================================================================
    """
    def updateDictionaries(self, rankings):

        self.updateDictionary(self.domainDictionary, rankings, self.DOMAIN)
        self.updateDictionary(self.phylumDictionary, rankings, self.PHYLUM)
        self.updateDictionary(self.classDictionary, rankings, self.CLASS)
        self.updateDictionary(self.orderDictionary, rankings, self.ORDER)
        self.updateDictionary(self.familyDictionary, rankings, self.FAMILY)
        self.updateDictionary(self.generaDictionary, rankings, self.GENERA)
        self.updateDictionary(self.speciesDictionary, rankings, self.SPECIES)
        self.updateDictionary(self.subspeciesDictionary, rankings, self.SUBSPECIES)

    """
    # =========================================================================

    UPDATE DICTIONARY
    -----------------


    PURPOSE
    -------

    Updates a particular dictionary with the passed taxonomic rankings. This
    dictionary will maintain the unique pricipal taxonomic rankings that have
    been observed. When a new taxonomic ranking is observed, it will be added
    to the dictionary. When a previously seen taxonomic ranking is observed, it
    will be ignored.


    INPUT
    -----

    [(STRING) -> (INT) DICTIONARY] [dictionary]
        The dictionary to update. This dictionary must agree with the passed
        [label].

    [STRING LIST] [rankings]
        A list of strings corresponding to specific taxonomic rankings. The
        format of these strings must be consistant with Kraken's 'translation'
        output. These strings must start with a rank identifier (d, p, c, p, f,
        g, s), then two "_" characters ("__"), then the name ("Bacteria"). For
        example, "d__Bacteria" and "s__Prevotella_enoeca".

    [STRING] [label]
        The label for a particular principal classification ranking (d, p, c,
        p, f, g, s). This label must agree with the passed [dictionary].


    RETURN
    ------

    [NONE]


    POST
    ----

    The passed [dictionary] will be updated, according to the passed
    [rankings] and [label].

    # =========================================================================
    """
    def updateDictionary(self, dictionary, rankings, label):

        for rank in rankings:

            if rank.startswith(str(label) + self.KRAKEN_SEPARATOR):

                # We found the right rank!
                # Check to see if it already exists in the dictory:
                if rank in dictionary:
                    dictionary[rank] += 1

                else:
                    dictionary[rank] = 1


"""
# =============================================================================

GENERATE RAREFACTION
--------------------


PURPOSE
-------

Generates the data necessary to construct rarefaction curves from Kraken files.


INPUT
-----

[FILE LOCATION] [untranslatedLocation]
    The file location of the untranslated Kraken output. This file is generated
    by running 'kraken' and may be filtered or unfiltered Kraken output.

[FILE LOCATION] [translatedLocation]
    The file location of the translated Kraken output. This file is generated
    by running 'kraken-translate'.

[SAMPLES LIST] [samples]
    A list of sub-sampling lists. These are the data points for which to
    generate rarefaction data.


RETURN
------

[NONE]


POST
----

The generated rarefaction data will be associated with the passed [samples].

# =============================================================================
"""
def generateRarefaction(untranslatedLocation, translatedLocation, samples):

    # Open the files.
    untranslatedFile = open(untranslatedLocation, 'r')
    translatedFile = open(translatedLocation, 'r')

    # Iterate over all the reads in the untranslated file.
    for untranslatedLine in untranslatedFile:

        number = random.random() # Generate a random number once per read!
        # We generate this random number once because we want all reads to
        # be in all sampling rate dictionaries that are "bigger" (have a
        # higher probability).

        # Is the read classified?
        # We only want to do this work once for all the sampling rates!
        if untranslatedLine[0] == CLASSIFIED:

            # Advance the translated file to find the translation.
            translatedLine = translatedFile.readline()
            
            # Tokenize the translation.
            tokens = translatedLine.strip().split()
            read = tokens[0].strip()
            classification = tokens[1].strip()

            rankings = classification.split("|")

        # Operate on each sampling rate:
        for i in range(0, len(samples)):

            # Do we add the read to the subsample (classified and unclassied)?
            # Include the read if its sampling rate is greater or equal.
            if number <= samples[i].rate:

                samples[i].numberOfReads += 1 # Increment the number of reads.

                # Is the read classified?
                # Update the dictionaries.
                if untranslatedLine[0] == CLASSIFIED:
                    samples[i].updateDictionaries(rankings)

    # Close input files.
    untranslatedFile.close()
    translatedFile.close()

"""
# =============================================================================

WRITE RESULTS
-------------


PURPOSE
-------

Writes the rarefaction data to output.


INPUT
-----

[FILE] [outputFile]
    The file to write the generated rarefaction data. This file must be open
    and ready for file writing.


RETURN
------

[NONE]


POST
----

The rarefaction data associated with the [samples] will be written to the
[outputFile].

# =============================================================================
"""
def writeResults(samples, outputFile):

    last = len(samples) - 1

    # Rates
    outputFile.write("rates,")
    for i in range(0, len(samples) - 1):
        outputFile.write(str(samples[i].rate) + ",")
    outputFile.write(str(samples[last].rate)) # last
    outputFile.write("\n")

    # Number of reads in each subsample:
    outputFile.write("reads,")
    for i in range(0, len(samples) - 1):
        outputFile.write(str(samples[i].numberOfReads) + ",")
    outputFile.write(str(samples[last].numberOfReads)) # last
    outputFile.write("\n")

    # Domains
    outputFile.write("domains,")
    for i in range(0, len(samples) - 1):
        outputFile.write(str(len(samples[i].domainDictionary)) + ",")
    outputFile.write(str(len(samples[last].domainDictionary))) # last
    outputFile.write("\n")

    # Phylums
    outputFile.write("phylums,")
    for i in range(0, len(samples) - 1):
        outputFile.write(str(len(samples[i].phylumDictionary)) + ",")
    outputFile.write(str(len(samples[last].phylumDictionary))) # last
    outputFile.write("\n")

    # Classes
    outputFile.write("classes,")
    for i in range(0, len(samples) - 1):
        outputFile.write(str(len(samples[i].classDictionary)) + ",")
    outputFile.write(str(len(samples[last].classDictionary))) # last
    outputFile.write("\n")

    # Orders
    outputFile.write("orders,")
    for i in range(0, len(samples) - 1):
        outputFile.write(str(len(samples[i].orderDictionary)) + ",")
    outputFile.write(str(len(samples[last].orderDictionary))) # last
    outputFile.write("\n")

    # Families
    outputFile.write("families,")
    for i in range(0, len(samples) - 1):
        outputFile.write(str(len(samples[i].familyDictionary)) + ",")
    outputFile.write(str(len(samples[last].familyDictionary))) # last
    outputFile.write("\n")

    # Genera
    outputFile.write("genera,")
    for i in range(0, len(samples) - 1):
        outputFile.write(str(len(samples[i].generaDictionary)) + ",")
    outputFile.write(str(len(samples[last].generaDictionary))) # last
    outputFile.write("\n")

    # Species
    outputFile.write("species,")
    for i in range(0, len(samples) - 1):
        outputFile.write(str(len(samples[i].speciesDictionary)) + ",")
    outputFile.write(str(len(samples[last].speciesDictionary))) # last
    outputFile.write("\n")

    # Subspecies
    outputFile.write("subspecies,")
    for i in range(0, len(samples) - 1):
        outputFile.write(str(len(samples[i].subspeciesDictionary)) + ",")
    outputFile.write(str(len(samples[last].subspeciesDictionary))) # last
    outputFile.write("\n")

"""
# =============================================================================

RUN
---


PURPOSE
-------

Runs the script. This is the main logical control of the script.


INPUT
-----

[FILE LOCATION] [untranslatedLocation]
    The file location of the untranslated Kraken output. This file is generated
    by running 'kraken' and may be filtered or unfiltered Kraken output.

[FILE LOCATION] [translatedLocation]
    The file location of the translated Kraken output. This file is generated
    by running 'kraken-translate'.

[FILE LOCATION] [outputLocation]
    The file location to write the generated rarefaction data.

[FLOAT] [rate]
    The sampling rate of this sample. This must be a number between (0, 1].


RETURN
------

[NONE]


POST
----

The rarefaction data will be generated and writen to the [outputLocation].

# =============================================================================
"""
def run(untranslatedLocation, translatedLocation, outputLocation, rate):

    # Check the untranslated file.
    if not os.path.isfile(untranslatedLocation):
        raise RuntimeError(
            "ERROR: Could not open input file: " + untranslatedLocation + "\n")

    # Check the translated file.
    if not os.path.isfile(translatedLocation):
        raise RuntimeError(
            "ERROR: Could not open input file: " + translatedLocation + "\n")

    # Check for optional values and set if necessary.
    if not rate:
        rate = DEFAULT_RATE

    # Check the rate is not within bounds.
    if (rate <= 0 or rate > 1):
        raise RuntimeError(
            "ERROR: The rate is not in range (0, 1]: " + str(rate) + "\n")

    # Open the output file.
    outputFile = open(outputLocation, 'w')

    # Initialize the samples:
    samples = []
    samplingPoints = int(1 / float(rate))

    for i in range(1, (samplingPoints + 1)):    # +1 to shift start off 0 to 1

        samples.append(Sample(i * rate))

    # Main logic:
    generateRarefaction(untranslatedLocation, translatedLocation, samples)
    writeResults(samples, outputFile)

    # Close output file.
    outputFile.close()

"""
# =============================================================================

PARSE

# =============================================================================
"""
def parse(parameters):

    untranslatedLocation = parameters.get(UNTRANSLATED)
    translatedLocation = parameters.get(TRANSLATED)
    outputLocation = parameters.get(OUTPUT)
    rate = parameters.get(RATE)

    run(untranslatedLocation, translatedLocation, outputLocation, rate)

"""
# =============================================================================

MAIN

# =============================================================================
"""
def main():

    # --- PARSER --- #
    parser = argparse.ArgumentParser(
        description=PROGRAM_DESCRIPTION,
        usage=PROGRAM_USAGE)

    # --- VERSION --- #
    parser.add_argument(
        VERSION_SHORT,
        VERSION_LONG,
        action='version',
        version='%(prog)s ' + str(__version__))

    # --- REQUIRED --- #
    required = parser.add_argument_group("REQUIRED")

    required.add_argument(
        UNTRANSLATED_SHORT,
        UNTRANSLATED_LONG,
        dest=UNTRANSLATED,
        help=UNTRANSLATED_HELP,
        type=str, required=True)

    required.add_argument(
        TRANSLATED_SHORT,
        TRANSLATED_LONG,
        dest=TRANSLATED,
        help=TRANSLATED_HELP,
        type=str, required=True)

    required.add_argument(
        OUTPUT_SHORT,
        OUTPUT_LONG,
        dest=OUTPUT,
        help=OUTPUT_HELP,
        type=str, required=True)

    # --- OPTIONAL --- #
    optional = parser.add_argument_group("OPTIONAL")

    optional.add_argument(
        RATE_SHORT,
        RATE_LONG,
        dest=RATE,
        help=RATE_HELP,
        type=float)

    args = parser.parse_args()
    parameters = vars(args)

    print("Rarefaction v" + str(__version__) + "\n")
    parse(parameters)

    print("\nComplete!")


"""
# =============================================================================
# =============================================================================
"""
if __name__ == '__main__':

    main()



