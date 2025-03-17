%chk=CALC_000032.chk
%mem=4GB
%NProcShared=1
#P SP HF/cc-pVQZ gfinput fchk=all out=wfx

CALC_000032 berilium HF cc-pVQZ

0 1
Be    0.0000   0.0000   0.0000

CALC_000032.wfx

