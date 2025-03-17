%chk=CALC_000085.chk
%mem=4GB
%NProcShared=1
#P SP HF/cc-pVTZ gfinput fchk=all out=wfx

CALC_000085 lithium HF cc-pVTZ

0 1
Li    0.000000   0.000000  -1.335000
Li    0.000000   0.000000   1.335000

CALC_000085.wfx

