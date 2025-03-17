%chk=CALC_000126.chk
%mem=4GB
%NProcShared=1
#P SP CASSCF(5,6)/cc-pVQZ gfinput fchk=all density=current iop(5/33=1) out=wfx

CALC_000126 lithium CASSCF(5,6) cc-pVQZ

1 2
Li    0.000000   0.000000  -1.335000
Li    0.000000   0.000000   1.335000

CALC_000126.wfx

