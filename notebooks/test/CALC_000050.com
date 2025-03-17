%chk=CALC_000050.chk
%mem=4GB
%NProcShared=1
#P SP HF/cc-pVDZ gfinput fchk=all out=wfx

CALC_000050 hydrogen HF cc-pVDZ

0 1
H    0.000000   0.000000  -0.370000
H    0.000000   0.000000   0.370000

CALC_000050.wfx

