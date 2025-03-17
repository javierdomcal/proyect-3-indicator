%chk=CALC_000042.chk
%mem=4GB
%NProcShared=1
#P SP HF/cc-pVQZ gfinput fchk=all out=wfx

CALC_000042 neon HF cc-pVQZ

0 1
Ne 0.0 0.0 0.0

CALC_000042.wfx

