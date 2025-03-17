%chk=CALC_000124.chk
%mem=4GB
%NProcShared=1
#P SP HF/cc-pVQZ gfinput fchk=all out=wfx

CALC_000124 lithium HF cc-pVQZ

1 2
Li    0.000000   0.000000  -1.335000
Li    0.000000   0.000000   1.335000

CALC_000124.wfx

