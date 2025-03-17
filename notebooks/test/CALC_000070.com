%chk=CALC_000070.chk
%mem=4GB
%NProcShared=1
#P SP HF/aug-cc-pVQZ gfinput fchk=all out=wfx

CALC_000070 hydrogen_2eq HF aug-cc-pVQZ

0 1
H    0.000000   0.000000  -0.750000
H    0.000000   0.000000   0.750000

CALC_000070.wfx

