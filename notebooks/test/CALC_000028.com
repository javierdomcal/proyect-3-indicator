%chk=CALC_000028.chk
%mem=4GB
%NProcShared=1
#P SP HF/cc-pVDZ gfinput fchk=all out=wfx

CALC_000028 berilium HF cc-pVDZ

0 1
Be    0.0000   0.0000   0.0000

CALC_000028.wfx

