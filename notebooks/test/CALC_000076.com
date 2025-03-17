%chk=CALC_000076.chk
%mem=4GB
%NProcShared=1
#P SP HF/aug-cc-pVQZ gfinput fchk=all out=wfx

CALC_000076 hydrogen_5eq HF aug-cc-pVQZ

0 1
H    0.000000   0.000000  -1.850000
H    0.000000   0.000000   1.850000

CALC_000076.wfx

