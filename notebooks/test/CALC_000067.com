%chk=CALC_000067.chk
%mem=4GB
%NProcShared=1
#P SP HF/cc-pVTZ gfinput fchk=all out=wfx

CALC_000067 hydrogen_2eq HF cc-pVTZ

0 1
H    0.000000   0.000000  -0.750000
H    0.000000   0.000000   0.750000

CALC_000067.wfx

