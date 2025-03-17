%chk=CALC_000055.chk
%mem=4GB
%NProcShared=1
#P SP HF/aug-cc-pVQZ gfinput fchk=all out=wfx

CALC_000055 hydrogen HF aug-cc-pVQZ

0 1
H    0.000000   0.000000  -0.370000
H    0.000000   0.000000   0.370000

CALC_000055.wfx

