%chk=CALC_000030.chk
%mem=4GB
%NProcShared=1
#P SP HF/cc-pVTZ gfinput fchk=all out=wfx

CALC_000030 berilium HF cc-pVTZ

0 1
Be    0.0000   0.0000   0.0000

CALC_000030.wfx

