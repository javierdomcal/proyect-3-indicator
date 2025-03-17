%chk=CALC_000073.chk
%mem=4GB
%NProcShared=1
#P SP HF/cc-pVTZ gfinput fchk=all out=wfx

CALC_000073 hydrogen_5eq HF cc-pVTZ

0 1
H    0.000000   0.000000  -1.850000
H    0.000000   0.000000   1.850000

CALC_000073.wfx

