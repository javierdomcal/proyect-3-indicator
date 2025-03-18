%chk=CALC_000007.chk
%mem=4GB
%NProcShared=1
#P SP CISD/cc-pVTZ gfinput fchk=all density=rhoci iop(9/40=7) iop(9/28=-1) use=l916 out=wfx

CALC_000007 helium CISD cc-pVTZ

0 1
He    0.0000   0.0000   0.0000

CALC_000007.wfx

