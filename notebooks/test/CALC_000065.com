%chk=CALC_000065.chk
%mem=4GB
%NProcShared=1
#P SP HF/cc-pVDZ gfinput fchk=all out=wfx

CALC_000065 hydrogen_2eq HF cc-pVDZ

0 1
H    0.000000   0.000000  -0.750000
H    0.000000   0.000000   0.750000

CALC_000065.wfx

