%chk=CALC_000123.chk
%mem=4GB
%NProcShared=1
#P SP HF/aug-cc-pVTZ gfinput fchk=all out=wfx

CALC_000123 lithium HF aug-cc-pVTZ

1 2
Li    0.000000   0.000000  -1.335000
Li    0.000000   0.000000   1.335000

CALC_000123.wfx

