%chk=CALC_000068.chk
%mem=4GB
%NProcShared=1
#P SP HF/aug-cc-pVTZ gfinput fchk=all out=wfx

CALC_000068 hydrogen_2eq HF aug-cc-pVTZ

0 1
H    0.000000   0.000000  -0.750000
H    0.000000   0.000000   0.750000

CALC_000068.wfx

