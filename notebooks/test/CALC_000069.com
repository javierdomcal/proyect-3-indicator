%chk=CALC_000069.chk
%mem=4GB
%NProcShared=1
#P SP HF/cc-pVQZ gfinput fchk=all out=wfx

CALC_000069 hydrogen_2eq HF cc-pVQZ

0 1
H    0.000000   0.000000  -0.750000
H    0.000000   0.000000   0.750000

CALC_000069.wfx

