%chk=CALC_000153.chk
%mem=4GB
%NProcShared=1
#P SP HF/aug-cc-pVQZ gfinput fchk=all out=wfx

CALC_000153 neon HF aug-cc-pVQZ

0 1
Ne 0.0 0.0 0.0

CALC_000153.wfx
