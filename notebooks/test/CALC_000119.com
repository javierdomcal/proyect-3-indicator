%chk=CALC_000119.chk
%mem=4GB
%NProcShared=1
#P SP CASSCF(6,6)/aug-cc-pVQZ gfinput fchk=all density=current iop(5/33=1) out=wfx

CALC_000119 lithium CASSCF(6,6) aug-cc-pVQZ

0 1
Li    0.000000   0.000000  -1.335000
Li    0.000000   0.000000   1.335000

CALC_000119.wfx

