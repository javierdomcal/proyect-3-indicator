%chk=CALC_000086.chk
%mem=4GB
%NProcShared=1
#P SP HF/aug-cc-pVTZ gfinput fchk=all out=wfx

CALC_000086 lithium HF aug-cc-pVTZ

0 1
Li    0.000000   0.000000  -1.335000
Li    0.000000   0.000000   1.335000

CALC_000086.wfx

