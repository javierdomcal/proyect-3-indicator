%chk=CALC_000087.chk
%mem=4GB
%NProcShared=1
#P SP HF/cc-pVQZ gfinput fchk=all out=wfx

CALC_000087 lithium HF cc-pVQZ

0 1
Li    0.000000   0.000000  -1.335000
Li    0.000000   0.000000   1.335000

CALC_000087.wfx

