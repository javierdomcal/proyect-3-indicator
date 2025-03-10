%chk=CALC_000113.chk
%mem=4GB
%NProcShared=1
#P SP CISD/cc-pVQZ gfinput fchk=all density=rhoci iop(9/40=7) iop(9/28=-1) use=l916 out=wfx

CALC_000113 lithium CISD cc-pVQZ

0 1
Li    0.000000   0.000000  -1.335000
Li    0.000000   0.000000   1.335000

CALC_000113.wfx

