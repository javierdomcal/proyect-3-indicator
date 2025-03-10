%chk=CALC_000026.chk
%mem=4GB
%NProcShared=1
#P SP HF/cc-pVQZ gfinput fchk=all out=wfx

CALC_000026 helium HF cc-pVQZ

0 1
He    0.0000   0.0000   0.0000

CALC_000026.wfx

