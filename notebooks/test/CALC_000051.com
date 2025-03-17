%chk=CALC_000051.chk
%mem=4GB
%NProcShared=1
#P SP HF/aug-cc-pVDZ gfinput fchk=all out=wfx

CALC_000051 hydrogen HF aug-cc-pVDZ

0 1
H    0.000000   0.000000  -0.370000
H    0.000000   0.000000   0.370000

CALC_000051.wfx

