%chk=CALC_000121.chk
%mem=4GB
%NProcShared=1
#P SP HF/aug-cc-pVDZ gfinput fchk=all out=wfx

CALC_000121 lithium HF aug-cc-pVDZ

1 2
Li    0.000000   0.000000  -1.335000
Li    0.000000   0.000000   1.335000

CALC_000121.wfx

