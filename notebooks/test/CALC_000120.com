%chk=CALC_000120.chk
%mem=4GB
%NProcShared=1
#P SP HF/cc-pVDZ gfinput fchk=all out=wfx

CALC_000120 lithium HF cc-pVDZ

1 2
Li    0.000000   0.000000  -1.335000
Li    0.000000   0.000000   1.335000

CALC_000120.wfx

