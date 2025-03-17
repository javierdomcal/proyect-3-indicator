%chk=CALC_000148.chk
%mem=4GB
%NProcShared=1
#P SP HF/cc-pVDZ gfinput fchk=all out=wfx

CALC_000148 neon HF cc-pVDZ

0 1
Ne 0.0 0.0 0.0

CALC_000148.wfx
