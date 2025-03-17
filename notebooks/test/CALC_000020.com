%chk=CALC_000020.chk
%mem=4GB
%NProcShared=1
#P SP HF/cc-pVDZ gfinput fchk=all out=wfx

CALC_000020 helium HF cc-pVDZ

0 1
He    0.0000   0.0000   0.0000

CALC_000020.wfx

