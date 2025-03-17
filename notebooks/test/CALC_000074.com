%chk=CALC_000074.chk
%mem=4GB
%NProcShared=1
#P SP HF/aug-cc-pVTZ gfinput fchk=all out=wfx

CALC_000074 hydrogen_5eq HF aug-cc-pVTZ

0 1
H    0.000000   0.000000  -1.850000
H    0.000000   0.000000   1.850000

CALC_000074.wfx

