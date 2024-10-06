# sampleids
Uniform sample ID parser

Available on PyPI at https://pypi.org/project/sampleids/
Available on Github at https://github.com/tmcqueen-materials/sampleids

## Quick Start

1. Install: `pip3 install sampleids`
2. In code, do:
```
from sampleids import parse as sid_parse, CONFIDENCE as sid_CONFIDENCE

res = sid_parse("AAA_BBB_YYYYMMDD_C_III_S_(QQQQQQQQQQ)-EE", ["AAA",...], ["BBB",...], ["III",...])
print(res) # will print the tuple SampleID(lab_id='AAA', tool_id='BBB', date='20241001', sample_id='C', provenance_id=['III'], split_id='S', parents=[SampleID(lab_id='', tool_id='', date='', sample_id='', provenance_id=[], split_id='', parents=[], extra='', raw='QQQQQQQQQQ', confidence=<CONFIDENCE.NONE: 0>, why='P_PARENT1_PI_V1_6L01_PI_V1_NOPARSE')], extra='EE', raw='AAA_BBB_20241001_C_III_S_(QQQQQQQQQQ)-EE', confidence=<CONFIDENCE.HIGH: 3>, why='P_PARENT1_PI_V1_6L01')

# You can check if confidence is greater than a minimum value, e.g.:
if res.confidence > sid_CONFIDENCE.LOW:
  print("Confidence is not low!")

# The "why" string gives a log of the code paths taken by the parser.
# If you find a case that fails to parse, and you think it should,
# or a case it parses incorrectly, be sure to include the why string!
print(res.why) # prints 'P_PARENT1_PI_V1_6L01'
```

## Specification

This module parses sample identifiers following the schema described at https://occamy.chemistry.jhu.edu/references/samples/index.php . It is a lenient parser, to account for variations observed in the real world, e.g. swapping of month and date, or swapping of identifier fragments.

## Version Compatibility
sampleids is compatible with all versions of Python 3.4+.

