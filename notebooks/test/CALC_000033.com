%chk=CALC_000033.chk
%mem=4GB
%NProcShared=1
#P SP HF/aug-cc-pVQZ gfinput fchk=all out=wfx

CALC_000033 berilium HF aug-cc-pVQZ

0 1
Be    0.0000   0.0000   0.0000

CALC_000033.wfx

