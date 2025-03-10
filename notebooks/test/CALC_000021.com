%chk=CALC_000021.chk
%mem=4GB
%NProcShared=1
#P SP CISD/cc-pVQZ gfinput fchk=all density=rhoci iop(9/40=7) iop(9/28=-1) use=l916 out=wfx

CALC_000021 helium CISD cc-pVQZ

0 1
He    0.0000   0.0000   0.0000

CALC_000021.wfx

