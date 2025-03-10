%chk=CALC_000027.chk
%mem=4GB
%NProcShared=1
#P SP HF/aug-cc-pVQZ gfinput fchk=all out=wfx

CALC_000027 helium HF aug-cc-pVQZ

0 1
He    0.0000   0.0000   0.0000

CALC_000027.wfx

